"""카카오 로컬 API 지오코딩 — 상호명 → 좌표·주소.

REST 키(settings.kakao_rest_api_key)가 없으면 조용히 비활성(None 반환) —
지도/좌표는 못 채우지만 장소명 수기 저장은 그대로 동작(우아한 폴백).
키 발급: https://developers.kakao.com → 앱 → REST API 키.
"""

import httpx

from app.config import settings

_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def is_enabled() -> bool:
    return bool(settings.kakao_rest_api_key)


def _headers() -> dict:
    return {"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"}


def _to_place(doc: dict) -> dict:
    """카카오 문서 → 우리 Place 필드."""
    # region_3depth_name(동) 우선, 없으면 category 뒤쪽
    region = None
    addr = doc.get("address_name") or ""
    parts = addr.split()
    if len(parts) >= 3:
        region = parts[2]  # 보통 '동'
    return {
        "name": doc.get("place_name"),
        "address": doc.get("road_address_name") or doc.get("address_name") or None,
        "region": region,
        "lat": float(doc["y"]) if doc.get("y") else None,
        "lng": float(doc["x"]) if doc.get("x") else None,
        "kakao_place_id": doc.get("id"),
    }


def search_places(query: str, size: int = 10) -> list[dict]:
    """키워드로 장소 검색 → 후보 리스트 (자동완성용). 키 없거나 실패 시 []."""
    if not is_enabled() or not query.strip():
        return []
    try:
        r = httpx.get(
            _KEYWORD_URL,
            params={"query": query, "size": size},
            headers=_headers(),
            timeout=5,
        )
        r.raise_for_status()
        return [_to_place(d) for d in r.json().get("documents", [])]
    except httpx.HTTPError:
        return []


def geocode_place(name: str) -> dict | None:
    """상호명 → 가장 관련 높은 장소 1건. 키 없거나 결과 없으면 None."""
    results = search_places(name, size=1)
    return results[0] if results else None
