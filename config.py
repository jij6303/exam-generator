import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///exam.db")
    # Render는 postgres:// 를 반환하지만 SQLAlchemy는 postgresql:// 필요
    SQLALCHEMY_DATABASE_URI = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
