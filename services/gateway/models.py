from pydantic_settings import BaseSettings , SettingsConfigDict



class Settings(BaseSettings):
    github_webhook_secret: str = ""


    # class Config:
    #     env_file = ".env"

    model_config = SettingsConfigDict(env_file=".env")