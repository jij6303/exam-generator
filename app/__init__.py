import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "로그인이 필요합니다."


def _migrate_schema(app):
    """users 테이블 스키마를 현재 모델에 맞게 마이그레이션한다.

    feature-#30에서 password_hash -> pin_hash, email 컬럼 제거가 이루어졌으나
    기존 DB는 db.create_all()로 자동 반영되지 않아 수동 마이그레이션이 필요하다.
    """
    from sqlalchemy import inspect, text

    with app.app_context():
        inspector = inspect(db.engine)
        if "users" not in inspector.get_table_names():
            return

        columns = {col["name"] for col in inspector.get_columns("users")}
        dialect = db.engine.dialect.name

        with db.engine.begin() as conn:
            if "password_hash" in columns and "pin_hash" not in columns:
                if dialect == "postgresql":
                    conn.execute(text("ALTER TABLE users RENAME COLUMN password_hash TO pin_hash"))
                else:
                    conn.execute(text("ALTER TABLE users RENAME COLUMN password_hash TO pin_hash"))

            if "email" in columns:
                if dialect == "postgresql":
                    conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS email"))
                # SQLite는 컬럼 삭제를 지원하지 않지만 email이 남아 있어도 동작에 지장 없음


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.exam.routes import exam_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)

    _migrate_schema(app)

    with app.app_context():
        db.create_all()

    return app
