"""로그인 실패 제한.

숫자 비밀번호처럼 경우의 수가 작은 비밀번호는 제한이 없으면 무차별 대입으로 뚫린다.
같은 (IP, 이름) 조합이 WINDOW 안에 MAX_FAILURES 번 틀리면 잠깐 잠근다.

키에 IP 를 섞는 이유: 이름만으로 잠그면 남이 일부러 틀려서 상대 계정을 잠가버릴 수 있다.
메모리에만 두므로 서버를 재시작하면 풀린다 — 단일 프로세스 개인 앱이라 이걸로 충분하다.
"""

import time
from collections import deque

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
LOCK_SECONDS = 5 * 60

_failures: dict[str, deque[float]] = {}
_locked_until: dict[str, float] = {}


def _key(ip: str | None, name: str) -> str:
    return f"{ip or '-'}|{name.strip().lower()}"


def seconds_locked(ip: str | None, name: str, now: float | None = None) -> int:
    """잠겨 있으면 남은 초, 아니면 0."""
    now = time.monotonic() if now is None else now
    until = _locked_until.get(_key(ip, name), 0)
    return max(0, int(until - now + 0.999))


def record_failure(ip: str | None, name: str, now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    key = _key(ip, name)
    q = _failures.setdefault(key, deque())
    q.append(now)
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MAX_FAILURES:
        _locked_until[key] = now + LOCK_SECONDS
        q.clear()


def reset(ip: str | None, name: str) -> None:
    key = _key(ip, name)
    _failures.pop(key, None)
    _locked_until.pop(key, None)


def clear_all() -> None:
    """테스트용."""
    _failures.clear()
    _locked_until.clear()
