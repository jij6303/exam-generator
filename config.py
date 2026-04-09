import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///exam.db")
    # postgres:// → postgresql:// (Render, neon.tech 등 레거시 스킴 대응)
    SQLALCHEMY_DATABASE_URI = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # neon.tech는 유휴 연결을 끊으므로 pool_pre_ping으로 재연결, pool_recycle로 수명 제한
    _is_postgres = not _db_url.startswith("sqlite")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        **({"connect_args": {"sslmode": "require"}} if _is_postgres else {}),
    }

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
