from pydantic import Field
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    bot_access_password: str = Field(alias="BOT_ACCESS_PASSWORD")
    database_path: str = Field(default="data/bot_state.sqlite3")


settings = Settings()
