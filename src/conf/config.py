
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')


class Settings(BaseSettings):
    sqlalchemy_database_url: str = 'postgresql+psycopg2://postgres:54321@localhost:5432/hw13'
    secret_key: str = 'secret_key'
    algorithm: str = 'HS256'
    mail_username: str = 'example@meta.ua'
    mail_password: str = 'password'
    mail_from: str = 'example@meta.ua'
    mail_port: int = 465
    mail_server: str = 'smtp.meta.ua'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cloudinary_name: str = 'SAadhsfhj'
    cloudinary_api_key: int = 971882847358355
    cloudinary_api_secret: str = 'dfdfdfdahfsjdg,h.P9g'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
