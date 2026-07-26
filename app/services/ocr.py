"""Apple Vision 로컬 OCR (macOS 전용).

이미지 bytes → 인식된 텍스트(줄바꿈 구분). 프라이버시상 로컬 처리(외부 전송 없음).
macOS 가 아니거나 pyobjc/Vision 이 없으면 is_available() 은 False, extract_text() 는 빈 문자열.
"""

import sys

_AVAILABLE = sys.platform == "darwin"
try:  # pragma: no cover - 플랫폼 의존
    if _AVAILABLE:
        import Foundation
        import Vision
except Exception:  # noqa: BLE001
    _AVAILABLE = False


def is_available() -> bool:
    return _AVAILABLE


def extract_text(
    image_bytes: bytes, languages: tuple[str, ...] = ("ko-KR", "en-US")
) -> str:
    """이미지 bytes → OCR 텍스트. 실패/미지원 시 빈 문자열."""
    if not _AVAILABLE:
        return ""
    data = Foundation.NSData.dataWithBytes_length_(image_bytes, len(image_bytes))
    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, {})
    request = Vision.VNRecognizeTextRequest.alloc().init()
    try:
        request.setRecognitionLanguages_(list(languages))
        request.setRecognitionLevel_(0)  # 0 = Accurate
        request.setUsesLanguageCorrection_(True)
    except Exception:  # noqa: BLE001
        pass

    ok, _err = handler.performRequests_error_([request], None)
    if not ok:
        return ""
    lines: list[str] = []
    for obs in request.results() or []:
        cands = obs.topCandidates_(1)
        if cands and len(cands):
            lines.append(str(cands[0].string()))
    return "\n".join(lines)
