"""비밀번호 해싱과 세션 관리.

- 비밀번호: 표준 라이브러리 scrypt. 외부 의존성 없이 메모리-하드 KDF 를 쓴다.
- 세션: 토큰 원문은 쿠키에만 있고 DB 에는 SHA-256 해시만 둔다.
  DB 가 유출돼도 세션을 탈취할 수 없고, 원문을 되돌릴 수도 없다.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

from sqlmodel import Session as DbSession
from sqlmodel import select

from app.models.core import Member, Session

SESSION_TTL = timedelta(days=30)
SESSION_COOKIE = "therich_session"

# scrypt 파라미터. n 을 키우면 느려지는 대신 무차별 대입이 비싸진다.
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    """'scrypt$n$r$p$salt$hash' 형태로 직렬화해 파라미터를 함께 보관한다."""
    if not password:
        raise ValueError("빈 비밀번호는 쓸 수 없습니다")
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """비밀번호가 맞는지. 형식이 깨졌거나 미설정이면 False(예외 대신)."""
    if not stored or not password:
        return False
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p),
            dklen=len(bytes.fromhex(hash_hex)),
        )
    except (ValueError, TypeError):
        return False
    # 타이밍 공격 방지를 위해 상수 시간 비교.
    return hmac.compare_digest(dk.hex(), hash_hex)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: DbSession, member: Member) -> str:
    """세션을 만들고 **원문 토큰**을 돌려준다. 이 값은 이후 어디에도 저장되지 않는다."""
    token = secrets.token_urlsafe(32)
    db.add(
        Session(
            member_id=member.id,
            token_hash=_hash_token(token),
            expires_at=datetime.utcnow() + SESSION_TTL,
        )
    )
    db.commit()
    return token


def resolve_session(db: DbSession, token: str | None) -> Member | None:
    """토큰 → 멤버. 만료·비활성·없는 토큰은 전부 None."""
    if not token:
        return None
    row = db.exec(
        select(Session).where(Session.token_hash == _hash_token(token))
    ).first()
    if row is None or row.expires_at < datetime.utcnow():
        return None
    member = db.get(Member, row.member_id)
    if member is None or not member.active:
        return None
    return member


def revoke_session(db: DbSession, token: str | None) -> None:
    if not token:
        return
    row = db.exec(
        select(Session).where(Session.token_hash == _hash_token(token))
    ).first()
    if row:
        db.delete(row)
        db.commit()


def purge_expired(db: DbSession) -> int:
    rows = db.exec(select(Session).where(Session.expires_at < datetime.utcnow())).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)
