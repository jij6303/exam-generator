from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pin_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exams = db.relationship("Exam", backref="user", lazy=True)
    wrong_answers = db.relationship("WrongAnswer", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    pdf_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    questions = db.relationship("Question", backref="exam", lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)

    # "multiple_choice" | "short_answer" | "ox"
    question_type = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)

    # 객관식 보기 (JSON string)
    options = db.Column(db.Text)

    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)


class WrongAnswer(db.Model):
    __tablename__ = "wrong_answers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 출처 시험 제목 (시험 삭제 후에도 유지하기 위해 텍스트로 저장)
    source_exam_title = db.Column(db.String(200))

    # 문제 데이터 직접 저장 (시험/문제 삭제와 무관하게 유지)
    question_type = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)

    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_mastered = db.Column(db.Boolean, default=False)
