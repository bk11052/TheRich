from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TheRich"
    database_url: str = "sqlite:///./therich.db"

    # 텔레그램 봇 (별도 프로세스). 토큰은 @BotFather 에서 발급받아 .env 에 넣는다.
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None  # 넛지 받을 채팅 id (/chatid 로 확인)
    telegram_default_account_id: int | None = None  # 기록할 기본 계좌 (미설정 시 자동)
    api_base_url: str = "http://127.0.0.1:8000"  # 봇이 호출할 백엔드


settings = Settings()
