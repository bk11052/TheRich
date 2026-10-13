"""계정 관리 CLI. 비밀번호는 인자로 받지 않고 입력 프롬프트로만 받는다
(셸 히스토리·프로세스 목록에 남지 않게).

  python -m app.manage list
  python -m app.manage set-password <이름>
  python -m app.manage add-partner <이름>
"""

import getpass
import sys

from sqlmodel import Session, select

from app.db import engine
from app.models.base import MemberRole
from app.models.core import Member
from app.services.auth import hash_password
from app.services.members import next_unused_color


def _prompt_password() -> str:
    first = getpass.getpass("비밀번호: ")
    if len(first) < 8:
        print("8자 이상이어야 합니다.")
        sys.exit(1)
    if first != getpass.getpass("다시 입력: "):
        print("두 입력이 다릅니다.")
        sys.exit(1)
    return first


def cmd_list() -> None:
    with Session(engine) as db:
        rows = db.exec(select(Member).order_by(Member.id)).all()
        if not rows:
            print("멤버가 없습니다.")
            return
        for m in rows:
            pw = "설정됨" if m.password_hash else "미설정"
            tg = m.telegram_chat_id or "-"
            state = "" if m.active else "  (비활성)"
            print(f"  [{m.id}] {m.name}  역할={m.role.value}  비번={pw}  텔레그램={tg}{state}")


def cmd_set_password(name: str) -> None:
    with Session(engine) as db:
        member = db.exec(select(Member).where(Member.name == name)).first()
        if member is None:
            print(f"'{name}' 멤버가 없습니다. python -m app.manage list 로 확인하세요.")
            sys.exit(1)
        member.password_hash = hash_password(_prompt_password())
        db.add(member)
        db.commit()
        print(f"{member.name} 의 비밀번호를 설정했습니다.")


def cmd_add_partner(name: str) -> None:
    with Session(engine) as db:
        if db.exec(select(Member).where(Member.name == name)).first():
            print(f"'{name}' 은 이미 있습니다.")
            sys.exit(1)
        member = Member(
            name=name,
            role=MemberRole.partner,
            color=next_unused_color(db),
            password_hash=hash_password(_prompt_password()),
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        print(f"동반자 '{member.name}' 추가 (id={member.id}, 색={member.color}).")
        print("텔레그램을 쓰려면 그 사람이 봇에 /chatid 를 보낸 뒤 대시보드에서 등록하세요.")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd, rest = args[0], args[1:]
    if cmd == "list":
        cmd_list()
    elif cmd == "set-password" and rest:
        cmd_set_password(rest[0])
    elif cmd == "add-partner" and rest:
        cmd_add_partner(rest[0])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
