from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TheRich"
    database_url: str = "sqlite:///./therich.db"
    # 업로드 사진 저장 폴더. 데모 DB 를 띄울 땐 uploads-demo 처럼 따로 둬서 실제 사진과 섞이지 않게 한다.
    upload_dir: str = "uploads"

    # 텔레그램 봇 (별도 프로세스). 토큰은 @BotFather 에서 발급받아 .env 에 넣는다.
    telegram_bot_token: str | None = None
    # 더 이상 봇이 쓰지 않는다(수신자는 member 테이블에서 읽음). 구버전 .env 호환용.
    telegram_chat_id: str | None = None
    # 텔레그램 봇처럼 사람이 아닌 클라이언트가 API 를 쓸 때의 토큰.
    # Authorization: Bearer <값> 으로 보내면 owner 권한을 얻는다.
    service_token: str | None = None
    telegram_default_account_id: int | None = None  # 기록할 기본 계좌 (미설정 시 자동)
    api_base_url: str = "http://127.0.0.1:8000"  # 봇이 호출할 백엔드

    # 카카오 로컬 API (지오코딩: 상호명 → 좌표·주소). REST 키를 kakao developers 에서 발급.
    # 프론트 지도용 JavaScript 키는 web/.env.local 의 NEXT_PUBLIC_KAKAO_JS_KEY 로 분리.
    kakao_rest_api_key: str | None = None


settings = Settings()
