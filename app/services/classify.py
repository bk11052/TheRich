import re

from sqlmodel import Session, select

from app.models.base import MatchType
from app.models.core import CategoryRule


def classify(session: Session, merchant: str | None) -> int | None:
    """가맹점명 → 규칙엔진으로 category_id 추정. 매칭 없으면 None.

    우선순위(priority) 높은 규칙부터 검사. AI는 여기서 안 잡히는 것만 나중에.
    """
    if not merchant:
        return None
    rules = session.exec(
        select(CategoryRule)
        .where(CategoryRule.enabled == True)  # noqa: E712
        .order_by(CategoryRule.priority.desc())
    ).all()
    for rule in rules:
        if rule.match_type == MatchType.exact and merchant == rule.pattern:
            return rule.category_id
        if rule.match_type == MatchType.contains and rule.pattern in merchant:
            return rule.category_id
        if rule.match_type == MatchType.regex:
            try:
                if re.search(rule.pattern, merchant):
                    return rule.category_id
            except re.error:
                continue
    return None
