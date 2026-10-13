"""데모 데이터 생성기 — 실제 DB 와 완전히 분리된 데모 DB 를 처음부터 만든다.

    python -m app.demo                 # therich-demo.db + uploads-demo/ 를 새로 생성
    python -m app.demo --password XYZ  # 데모 계정 비밀번호를 직접 지정

그다음 백엔드를 데모 DB 로 띄운다 (실제 백엔드는 먼저 끈다 — 같은 8000 포트):

    DATABASE_URL=sqlite:///./therich-demo.db UPLOAD_DIR=uploads-demo \\
      .venv/bin/python3 -m uvicorn app.main:app --reload

- 오늘 기준 최근 4개월: 개인 지출·수입·예산·순자산 추이, 데이트비용과 추억(사진·장소·태그·메모).
- 데이트비용 한도는 매달 80만 원. '넘은 달 / 거의 다 쓴 달 / 여유 있는 달'이 모두 보이게 한다.
- 계정: demo(주인), demo-partner(동반자). 비밀번호는 실행마다 새로 만들어 출력한다 —
  공개 레포에 비밀번호를 적어두지 않기 위해서다.
- 모든 금액·가맹점·장소는 가짜다. 실제 개인정보를 넣지 않는다(CLAUDE.md 규칙).

주의: app.config 는 import 시점에 환경변수를 읽는다. 그래서 이 파일은 데모 경로를
환경변수에 먼저 넣은 다음에야 app 모듈을 import 한다(파일 맨 위에서 import 하지 않는 이유).
"""

import argparse
import os
import random
import secrets
import shutil
import sys
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = "therich-demo.db"
DEFAULT_UPLOADS = "uploads-demo"
MONTHS = 4
DATE_LIMIT = 800_000  # 데모 커플의 월 데이트비용 한도

# ---------- 데이트비용 재료 (전부 가짜) ----------
# (kind, merchant, 최소, 최대, (장소이름, 지역, 위도, 경도), 사진색1, 사진색2)
DATE_POOL = {
    "meal": [
        ("을지로 노포 고깃집", 48_000, 86_000, ("을지로 노포 고깃집", "을지로", 37.5663, 126.9910), "#b1442e", "#e08c4a"),
        ("연남동 생면 파스타", 38_000, 62_000, ("연남동 생면 파스타", "연남동", 37.5627, 126.9255), "#c2571a", "#f2b35c"),
        ("망원 수제버거", 27_000, 41_000, ("망원 수제버거", "망원동", 37.5559, 126.9036), "#8a5a2b", "#d9a05b"),
        ("이태원 타코바", 31_000, 49_000, ("이태원 타코바", "이태원", 37.5345, 126.9946), "#2e9e5b", "#a3d977"),
        ("성수 이자카야", 52_000, 88_000, ("성수 이자카야", "성수동", 37.5446, 127.0557), "#5b3a8a", "#b07ad9"),
    ],
    "cafe": [
        ("블루보틀 성수", 9_500, 16_000, ("블루보틀 성수", "성수동", 37.5481, 127.0453), "#2f6df6", "#7fb0ff"),
        ("연희동 디저트카페", 14_000, 24_000, ("연희동 디저트카페", "연희동", 37.5683, 126.9314), "#d9688a", "#f6b6c8"),
        ("서촌 한옥카페", 12_000, 19_000, ("서촌 한옥카페", "서촌", 37.5797, 126.9705), "#6b5b45", "#c9b28a"),
    ],
    "activity": [
        ("CGV 용산아이파크몰", 26_000, 38_000, ("CGV 용산아이파크몰", "용산", 37.5292, 126.9648), "#1f2937", "#4b5563"),
        ("리움미술관", 24_000, 30_000, ("리움미술관", "한남동", 37.5384, 126.9990), "#334155", "#94a3b8"),
        ("홍대 방탈출", 44_000, 52_000, ("홍대 방탈출", "홍대", 37.5563, 126.9236), "#0f172a", "#7c3aed"),
        ("뚝섬 한강 피크닉", 14_000, 29_000, ("뚝섬한강공원", "뚝섬", 37.5292, 127.0669), "#0f9fb0", "#7dd3c0"),
        ("롯데월드", 108_000, 128_000, ("롯데월드", "잠실", 37.5111, 127.0982), "#e5484d", "#ffb36b"),
    ],
}
TRIP = [
    ("강릉 오션뷰 숙소", 168_000, 214_000, ("강릉 안목해변", "강릉", 37.7720, 128.9471), "#0369a1", "#7dd3fc"),
    ("주문진 회센터", 62_000, 88_000, ("주문진 수산시장", "강릉", 37.8920, 128.8270), "#0e7490", "#67e8f9"),
]
MEMOS = {
    "meal": ["여기 또 오자", "웨이팅 40분 했지만 그럴 가치", "사장님이 서비스 주심", "기념일 저녁", "비 와서 더 분위기 있었음"],
    "cafe": ["창가 자리 성공", "디저트가 메인이었음", "사진 잘 나오는 곳", "오래 수다 떨기 좋음"],
    "activity": ["둘 다 소리 지름", "생각보다 재밌었다", "다음엔 아침 일찍 가기", "노을 예뻤음", "사람 많았지만 좋았다"],
    "trip": ["첫 여행", "바다 소리 들으며 잠듦", "다음엔 2박 하자"],
}
TAGS = [("데이트", "#ec4899"), ("맛집", "#f97316"), ("카페", "#a16207"), ("액티비티", "#2563eb"), ("여행", "#0891b2")]
TAG_FOR = {"meal": ["데이트", "맛집"], "cafe": ["데이트", "카페"], "activity": ["데이트", "액티비티"], "trip": ["데이트", "여행"]}


def _photo_svg(title: str, sub: str, c1: str, c2: str) -> str:
    """기록 갤러리용 가짜 사진. 직접 만든 정적 파일이라 SVG 여도 안전하다
    (사용자가 올리는 SVG 를 막는 것과는 별개)."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect width="800" height="800" fill="url(#g)"/>
<circle cx="640" cy="170" r="120" fill="#fff" opacity=".16"/>
<circle cx="120" cy="640" r="200" fill="#fff" opacity=".09"/>
<text x="64" y="650" font-family="-apple-system,system-ui,sans-serif" font-size="60" font-weight="700" fill="#fff">{escape(title)}</text>
<text x="64" y="712" font-family="-apple-system,system-ui,sans-serif" font-size="30" fill="#fff" opacity=".85">{escape(sub)}</text>
</svg>"""


def _recent_months(today: date, n: int) -> list[tuple[int, int]]:
    out, y, m = [], today.year, today.month
    for _ in range(n):
        out.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return list(reversed(out))


def _round(n: float, unit: int = 100) -> int:
    return int(round(n / unit) * unit)


def _guard(db: Path, uploads: Path) -> None:
    """실제 데이터를 지우지 않도록, 이름에 demo 가 들어간 경로만 허용한다."""
    if db.name == "therich.db" or "demo" not in db.name or db.suffix != ".db":
        sys.exit(f"거부: 데모 DB 파일 이름에는 'demo' 가 들어가야 합니다 (받은 값: {db.name}).")
    if uploads.name == "uploads" or "demo" not in uploads.name:
        sys.exit(f"거부: 데모 사진 폴더 이름에는 'demo' 가 들어가야 합니다 (받은 값: {uploads.name}).")


def build(today: date, upload_dir: Path, password: str | None) -> dict:
    # 여기서부터 app import — 환경변수가 이미 데모 경로를 가리키고 있다.
    from sqlmodel import Session, select

    from app import seed as base_seed
    from app import seed_demo
    from app.db import engine
    from app.models.base import AccountSide, AccountType, CategoryKind, MemberRole, TxnSource, TxnType
    from app.models.core import Account, Budget, Category, Member, NetWorthSnapshot, Transaction
    from app.models.lifelog import Photo, Place, Tag, TransactionTag
    from app.services.auth import hash_password
    from app.services.classify import classify

    base_seed.seed()  # 카테고리 + 자동분류 규칙
    rng = random.Random(20261014)  # 결정적 — 같은 날 다시 돌리면 같은 데모
    months = _recent_months(today, MONTHS)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stats = {"personal": 0, "income": 0, "date": 0, "records": 0, "photos": 0}

    def last_day(y: int, m: int) -> int:
        d = monthrange(y, m)[1]
        return min(d, today.day) if (y, m) == (today.year, today.month) else d

    with Session(engine) as s:
        # --- 계좌 ---
        accounts = {}
        for name, atype, side, balance, inst in seed_demo.ACCOUNTS + [
            ("토스증권 데모", AccountType.securities, AccountSide.asset, 3_200_000, "토스증권"),
        ]:
            a = Account(name=name, type=atype, side=side, balance=balance, institution=inst)
            s.add(a)
            accounts[name] = a
        s.commit()
        for a in accounts.values():
            s.refresh(a)
        card = accounts["현대카드 M"]
        bank = accounts["신한 주거래"]

        cats = {c.name: c for c in s.exec(select(Category)).all()}
        salary_cat = cats.get("급여")

        # --- 개인 지출·수입 ---
        for y, m in months:
            ld = last_day(y, m)
            for merchant, lo, hi, count in seed_demo.EXPENSE_POOL:
                for _ in range(count):
                    d = rng.randint(1, ld)
                    s.add(Transaction(
                        account_id=card.id, type=TxnType.expense,
                        amount=_round(rng.randint(lo, hi)),
                        occurred_at=datetime(y, m, d, rng.randint(8, 22), rng.randint(0, 59)),
                        merchant=merchant, category_id=classify(s, merchant),
                        source=rng.choice([TxnSource.manual, TxnSource.telegram_ocr]),
                    ))
                    stats["personal"] += 1
            if 25 <= ld:
                s.add(Transaction(
                    account_id=bank.id, type=TxnType.income, amount=2_500_000,
                    occurred_at=datetime(y, m, 25, 9, 0), merchant="급여 (데모)",
                    category_id=salary_cat.id if salary_cat else None,
                ))
                stats["income"] += 1
            for cat_name, amount in seed_demo.BUDGETS:
                if cat_name in cats:
                    s.add(Budget(category_id=cats[cat_name].id, period_month=f"{y}-{m:02d}", amount=amount))
        s.commit()

        # --- 데이트비용 ---
        date_cat = Category(name="데이트", kind=CategoryKind.expense, is_shared=True, color="#ec4899")
        s.add(date_cat)
        tags = {}
        for name, color in TAGS:
            t = Tag(name=name, color=color)
            s.add(t)
            tags[name] = t
        s.commit()
        s.refresh(date_cat)
        for t in tags.values():
            s.refresh(t)

        def add_date(kind: str, item: tuple, when: datetime, with_record: bool) -> int:
            merchant, lo, hi, place_info, c1, c2 = item
            amount = _round(rng.randint(lo, hi), 1000 if hi >= 100_000 else 500)
            txn = Transaction(
                account_id=card.id, type=TxnType.expense, amount=amount, occurred_at=when,
                merchant=merchant, category_id=date_cat.id, source=TxnSource.telegram_ocr,
            )
            s.add(txn)
            s.commit()
            s.refresh(txn)
            stats["date"] += 1
            if not with_record:
                return amount
            pname, region, lat, lng = place_info
            place = Place(name=pname, region=region, lat=lat, lng=lng)
            s.add(place)
            s.commit()
            s.refresh(place)
            txn.place_id = place.id
            txn.memo = rng.choice(MEMOS[kind])
            for i in range(2 if rng.random() < 0.3 else 1):
                fname = f"demo-{txn.id}-{i}.svg"
                (upload_dir / fname).write_text(
                    _photo_svg(merchant, f"{when.month}월 {when.day}일", c1 if i == 0 else c2, c2 if i == 0 else c1),
                    encoding="utf-8",
                )
                s.add(Photo(transaction_id=txn.id, file_path=f"/uploads/{fname}", taken_at=when))
                stats["photos"] += 1
            for tag_name in TAG_FOR[kind]:
                s.add(TransactionTag(transaction_id=txn.id, tag_id=tags[tag_name].id))
            s.add(txn)
            s.commit()
            stats["records"] += 1
            return amount

        spend_by_month: dict[tuple[int, int], int] = {}
        for idx, (y, m) in enumerate(months):
            total = 0
            ld = last_day(y, m)
            for d in range(1, ld + 1):
                wd = date(y, m, d).weekday()  # 0=월 … 6=일
                p = 0.62 if wd >= 4 else 0.12  # 금·토·일에 주로 만난다
                if rng.random() > p:
                    continue
                plan = ["meal"] + (["cafe"] if rng.random() < 0.55 else []) + (["activity"] if rng.random() < 0.4 else [])
                hour = rng.choice([12, 13, 17, 18])
                for kind in plan:
                    item = rng.choice(DATE_POOL[kind])
                    total += add_date(kind, item, datetime(y, m, d, hour, rng.choice([0, 10, 20, 30, 40])), rng.random() < 0.55)
                    hour = min(hour + 2, 22)
            # 두 달 전엔 1박 여행
            if idx == 1:
                d = min(18, ld)
                for j, item in enumerate(TRIP):
                    total += add_date("trip", item, datetime(y, m, d, 15 + j * 4), True)
            spend_by_month[(y, m)] = total

        # 한도는 실제처럼 매달 같은 금액. 그 고정 한도로 지난 달들에서
        # '초과 / 거의 다 씀(80%↑) / 여유'가 다 보이는지 확인하고, 무작위 결과로
        # 하나라도 빠지면 그때만 지난 달 한도를 소진액에 맞춰 조정한다.
        def state_of(spent: int, limit: int) -> str:
            r = spent / limit
            return "over" if r >= 1 else "warning" if r >= 0.8 else "ok"

        limits = {k: DATE_LIMIT for k in months}
        past = months[:-1]
        if {state_of(spend_by_month[k], DATE_LIMIT) for k in past} != {"over", "warning", "ok"}:
            ordered = sorted(past, key=lambda k: spend_by_month[k], reverse=True)
            for k, ratio in zip(ordered, (1.14, 0.84, 0.6)):  # 가장 많이 쓴 달을 초과로
                limits[k] = _round(spend_by_month[k] / ratio, 10_000)
        for (y, m), limit in limits.items():
            s.add(Budget(category_id=date_cat.id, period_month=f"{y}-{m:02d}", amount=limit))
        s.commit()

        # --- 순자산 추이 (최근 6개 월말) ---
        nw = 7_100_000
        for back in range(6, 0, -1):
            y, m = today.year, today.month - back
            while m <= 0:
                y, m = y - 1, m + 12
            debt = rng.randint(250_000, 650_000)  # 카드 대금 등
            s.add(NetWorthSnapshot(
                snapshot_date=date(y, m, monthrange(y, m)[1]),
                total_assets=nw + debt, total_liabilities=debt, net_worth=nw,
            ))
            nw += rng.randint(250_000, 520_000)
        s.commit()

        # --- 계정 ---
        pw_owner = password or secrets.token_urlsafe(9)
        pw_partner = password or secrets.token_urlsafe(9)
        s.add(Member(name="demo", role=MemberRole.owner, is_self=True, password_hash=hash_password(pw_owner)))
        s.add(Member(name="demo-partner", role=MemberRole.partner, password_hash=hash_password(pw_partner)))
        s.commit()

    seed_demo._seed_cards()
    return {"stats": stats, "spend": spend_by_month, "pw_owner": pw_owner, "pw_partner": pw_partner}


def main() -> None:
    parser = argparse.ArgumentParser(description="데모 DB 를 처음부터 새로 만든다 (실제 DB 는 건드리지 않음).")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"데모 DB 파일 (기본 {DEFAULT_DB})")
    parser.add_argument("--uploads", default=DEFAULT_UPLOADS, help=f"데모 사진 폴더 (기본 {DEFAULT_UPLOADS})")
    parser.add_argument("--password", help="데모 계정 비밀번호 (생략 시 무작위 생성)")
    args = parser.parse_args()

    os.chdir(ROOT)  # alembic.ini·상대경로 기준
    db, uploads = Path(args.db), Path(args.uploads)
    _guard(db, uploads)

    # 처음부터 새로. 위의 _guard 가 'demo' 이름만 통과시키므로 실제 데이터는 지울 수 없다.
    if db.exists():
        db.unlink()
    if uploads.exists():
        shutil.rmtree(uploads)

    # app 을 import 하기 전에 데모 경로를 환경변수로 고정 (.env 보다 환경변수가 우선).
    # 절대경로로 바꿔 넣는다 — 'sqlite:///./' 뒤에 절대경로를 붙이면 주소가 깨진다.
    os.environ["DATABASE_URL"] = f"sqlite:///{db.resolve().as_posix()}"
    os.environ["UPLOAD_DIR"] = uploads.resolve().as_posix()

    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")

    result = build(date.today(), uploads, args.password)
    st = result["stats"]

    print()
    print("데모 DB 를 만들었어요.")
    print(f"  DB      : {db}")
    print(f"  사진    : {uploads}/")
    print(f"  개인지출 {st['personal']}건 · 수입 {st['income']}건 · 데이트비용 {st['date']}건")
    print(f"  추억 {st['records']}건 (사진 {st['photos']}장)")
    for (y, m), spent in result["spend"].items():
        print(f"    {y}-{m:02d} 데이트비용 {spent:,}원")
    print()
    print("로그인 계정")
    print(f"  주인     demo          / {result['pw_owner']}")
    print(f"  동반자   demo-partner  / {result['pw_partner']}")
    print()
    print("실제 백엔드를 끄고, 데모 DB 로 띄우세요:")
    print(f"  DATABASE_URL=sqlite:///./{db.as_posix()} UPLOAD_DIR={uploads.as_posix()} \\")
    print("    .venv/bin/python3 -m uvicorn app.main:app --reload")
    print("다 보고 나면 같은 방식으로 실제 백엔드를 다시 띄우면 됩니다 (환경변수 없이).")


if __name__ == "__main__":
    main()
