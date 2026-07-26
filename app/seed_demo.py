"""데모용 계좌·거래·예산 시드 (개발/프리뷰용).

실행: python -m app.seed_demo
기존 거래가 있으면 건너뜀(idempotent). 카테고리는 app.seed 를 먼저 실행해 채워둘 것.
거래는 merchant 만 넣고 category_id 는 규칙엔진(classify)이 자동 채움 — 실제 입력 경로와 동일.
"""

import random
from datetime import date, datetime

from sqlmodel import Session, select

from app.db import engine
from app.models.base import AccountSide, AccountType, TxnSource, TxnType
from app.models.core import Account, Budget, Category, NetWorthSnapshot, Transaction
from app.services.classify import classify

# 데모 기준 월 (오늘=2026-07-26 가정). 결정적 재현을 위해 고정.
YEAR, MONTH, TODAY = 2026, 7, 26

# (name, type, side, balance원, institution)
ACCOUNTS = [
    ("신한 주거래", AccountType.bank, AccountSide.asset, 8_420_000, "신한은행"),
    ("현대카드 M", AccountType.card, AccountSide.liability, 0, "현대카드"),
    ("현금 지갑", AccountType.cash, AccountSide.asset, 130_000, None),
]

# (merchant, 금액원 범위, 대략 건수) — merchant 는 seed.py 규칙과 매칭되도록 선택
EXPENSE_POOL = [
    ("스타벅스 강남점", 4_500, 7_500, 6),
    ("메가커피", 2_000, 3_500, 4),
    ("배달의민족", 12_000, 28_000, 5),
    ("쿠팡이츠", 11_000, 24_000, 3),
    ("GS25 역삼", 3_000, 12_000, 6),
    ("이마트 성수", 25_000, 78_000, 3),
    ("올리브영", 15_000, 45_000, 2),
    ("카카오 T 택시", 6_000, 19_000, 4),
    ("티머니 교통", 1_250, 3_200, 8),
    ("김밥천국", 6_000, 11_000, 3),
    ("삼겹살집 회식", 32_000, 68_000, 2),
    ("CGV 용산", 14_000, 28_000, 1),
    ("무신사", 39_000, 120_000, 2),
    ("넷플릭스", 13_500, 13_500, 1),
    ("Claude Pro", 29_000, 29_000, 1),
    ("올리브영 약국", 8_000, 22_000, 1),
    ("교보문고", 18_000, 43_000, 1),
]

# 순자산 추이 스냅샷 (date, net_worth원) — 현재(8,550,000)까지 상승 추세
SNAPSHOTS = [
    (date(2026, 2, 28), 6_900_000),
    (date(2026, 3, 31), 7_250_000),
    (date(2026, 4, 30), 7_600_000),
    (date(2026, 5, 31), 7_950_000),
    (date(2026, 6, 30), 8_150_000),
    (date(2026, 7, 26), 8_550_000),
]

# (category_name, 예산원)
BUDGETS = [
    ("식비", 500_000),
    ("배달", 200_000),
    ("카페/간식", 120_000),
    ("교통", 150_000),
    ("쇼핑", 300_000),
    ("마트/장보기", 250_000),
]


def seed_demo() -> None:
    rng = random.Random(42)
    month_str = f"{YEAR:04d}-{MONTH:02d}"

    with Session(engine) as session:
        # --- 순자산 스냅샷 (거래와 독립적으로 시드) ---
        if not session.exec(select(NetWorthSnapshot)).first():
            for snap_date, net in SNAPSHOTS:
                session.add(
                    NetWorthSnapshot(
                        snapshot_date=snap_date,
                        total_assets=net,
                        total_liabilities=0,
                        net_worth=net,
                    )
                )
            session.commit()
            print(f"snapshots: +{len(SNAPSHOTS)}")

        if session.exec(select(Transaction)).first():
            print("거래가 이미 존재 — 계좌/거래/예산 시드 건너뜀")
            return

        # --- 계좌 ---
        accounts = []
        for name, atype, side, balance, inst in ACCOUNTS:
            acc = Account(
                name=name, type=atype, side=side, balance=balance, institution=inst
            )
            session.add(acc)
            accounts.append(acc)
        session.commit()
        for a in accounts:
            session.refresh(a)
        card = next(a for a in accounts if a.type == AccountType.card)
        cash = next(a for a in accounts if a.type == AccountType.cash)
        bank = next(a for a in accounts if a.type == AccountType.bank)

        # --- 지출 거래 (merchant→classify 자동분류) ---
        n_txn = 0
        for merchant, lo, hi, count in EXPENSE_POOL:
            for _ in range(count):
                day = rng.randint(1, TODAY)
                hour = rng.randint(8, 22)
                amount = rng.randint(lo // 100, hi // 100) * 100  # 100원 단위
                acc = rng.choice([card, card, cash])  # 대부분 카드
                cat_id = classify(session, merchant)
                session.add(
                    Transaction(
                        account_id=acc.id,
                        type=TxnType.expense,
                        amount=amount,
                        occurred_at=datetime(YEAR, MONTH, day, hour, rng.randint(0, 59)),
                        merchant=merchant,
                        category_id=cat_id,
                        source=rng.choice(
                            [TxnSource.telegram_ocr, TxnSource.manual, TxnSource.csv]
                        ),
                    )
                )
                n_txn += 1

        # --- 수입 (급여) ---
        salary_cat = session.exec(select(Category).where(Category.name == "급여")).first()
        session.add(
            Transaction(
                account_id=bank.id,
                type=TxnType.income,
                amount=3_800_000,
                occurred_at=datetime(YEAR, MONTH, 25, 9, 0),
                merchant="급여 입금",
                category_id=salary_cat.id if salary_cat else None,
                source=TxnSource.manual,
            )
        )
        n_txn += 1

        # --- 예산 ---
        n_budget = 0
        cat_by_name = {c.name: c for c in session.exec(select(Category)).all()}
        for cat_name, amount in BUDGETS:
            cat = cat_by_name.get(cat_name)
            if cat is None:
                continue
            session.add(
                Budget(category_id=cat.id, period_month=month_str, amount=amount)
            )
            n_budget += 1

        session.commit()
        print(f"accounts: +{len(accounts)}  transactions: +{n_txn}  budgets: +{n_budget}")
        print(f"기준월: {month_str}")


if __name__ == "__main__":
    seed_demo()
