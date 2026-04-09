import json
import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Exam, Question, WrongAnswer
from app.services.pdf_service import extract_text, get_pdf_info, extract_text_by_pages
from app.services.ai_service import generate_questions

exam_bp = Blueprint("exam", __name__)


@exam_bp.route("/")
@login_required
def dashboard():
    exams = Exam.query.filter_by(user_id=current_user.id).order_by(Exam.created_at.desc()).all()
    wrong_count = WrongAnswer.query.filter_by(user_id=current_user.id, is_mastered=False).count()
    return render_template("exam/dashboard.html", exams=exams, wrong_count=wrong_count)


@exam_bp.route("/upload/analyze", methods=["POST"])
@login_required
def analyze_pdf():
    """PDF를 미리 저장하고 페이지 수 및 챕터 정보를 반환한다."""
    file = request.files.get("pdf")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDF 파일이 필요합니다."}), 400

    filename = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    try:
        info = get_pdf_info(save_path)
    except Exception:
        os.remove(save_path)
        return jsonify({"error": "PDF 분석에 실패했습니다."}), 500

    return jsonify({"tmp_filename": filename, **info})


@exam_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    is_demo = not current_app.config.get("ANTHROPIC_API_KEY")
    if request.method == "POST":
        tmp_filename = request.form.get("tmp_filename", "").strip()
        text = ""
        filename = None

        if tmp_filename:
            # analyze 단계에서 이미 저장된 파일 재사용
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], tmp_filename)
            if not os.path.isfile(save_path):
                flash("업로드된 파일을 찾을 수 없습니다. 다시 시도해주세요.", "danger")
                return render_template("exam/upload.html", is_demo=is_demo)
            filename = tmp_filename

            page_start = int(request.form.get("page_start") or 1)
            page_end_raw = request.form.get("page_end", "").strip()
            page_end = int(page_end_raw) if page_end_raw else 9999

            try:
                text = extract_text_by_pages(save_path, page_start, page_end)
            except Exception:
                flash("PDF 텍스트 추출에 실패했습니다.", "danger")
                return render_template("exam/upload.html", is_demo=is_demo)

        else:
            # JS 없이 직접 폼 제출한 경우 (fallback)
            file = request.files.get("pdf")
            if file and file.filename:
                if not file.filename.lower().endswith(".pdf"):
                    flash("PDF 파일만 업로드 가능합니다.", "danger")
                    return render_template("exam/upload.html", is_demo=is_demo)

                filename = f"{uuid.uuid4().hex}.pdf"
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)

                try:
                    text = extract_text(save_path)
                except Exception:
                    flash("PDF 텍스트 추출에 실패했습니다.", "danger")
                    return render_template("exam/upload.html", is_demo=is_demo)
            elif not is_demo:
                flash("PDF 파일을 선택해주세요.", "danger")
                return render_template("exam/upload.html", is_demo=is_demo)

        num_mc = int(request.form.get("num_multiple_choice", 5))
        num_sa = int(request.form.get("num_short_answer", 3))
        num_ox = int(request.form.get("num_ox", 2))

        try:
            raw_questions = generate_questions(text, num_mc, num_sa, num_ox)
        except Exception as e:
            flash(f"문제 생성에 실패했습니다: {e}", "danger")
            return render_template("exam/upload.html", is_demo=is_demo)

        file_obj = request.files.get("pdf")
        title = request.form.get("title") or (file_obj.filename if file_obj and file_obj.filename else "데모 시험")
        exam = Exam(title=title, pdf_filename=filename, user_id=current_user.id)
        db.session.add(exam)
        db.session.flush()

        for i, q in enumerate(raw_questions):
            question = Question(
                exam_id=exam.id,
                question_type=q["question_type"],
                question_text=q["question_text"],
                options=json.dumps(q.get("options"), ensure_ascii=False) if q.get("options") else None,
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", ""),
                order=i,
            )
            db.session.add(question)

        db.session.commit()
        return redirect(url_for("exam.quiz", exam_id=exam.id))

    return render_template("exam/upload.html", is_demo=is_demo)


@exam_bp.route("/quiz/<int:exam_id>")
@login_required
def quiz(exam_id):
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order).all()
    for q in questions:
        q.options_list = json.loads(q.options) if q.options else []
    return render_template("exam/quiz.html", exam=exam, questions=questions)


@exam_bp.route("/quiz/<int:exam_id>/submit", methods=["POST"])
@login_required
def submit(exam_id):
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.order).all()

    results = []
    score = 0
    for q in questions:
        user_answer = request.form.get(f"answer_{q.id}", "").strip()
        is_correct = _check_answer(q, user_answer)
        if is_correct:
            score += 1
        results.append({
            "question": q,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "options_list": json.loads(q.options) if q.options else [],
        })

    # 오답 자동 저장
    for r in results:
        if not r["is_correct"]:
            q = r["question"]
            existing = WrongAnswer.query.filter_by(
                user_id=current_user.id,
                question_text=q.question_text,
                correct_answer=q.correct_answer,
            ).first()
            if existing:
                existing.added_at = datetime.utcnow()
                existing.is_mastered = False
            else:
                db.session.add(WrongAnswer(
                    user_id=current_user.id,
                    source_exam_title=exam.title,
                    question_type=q.question_type,
                    question_text=q.question_text,
                    options=q.options,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation,
                ))
    db.session.commit()

    wrong_count = sum(1 for r in results if not r["is_correct"])
    total = len(questions)
    return render_template(
        "exam/result.html",
        exam=exam, results=results, score=score, total=total, wrong_count=wrong_count,
    )


# ── 오답노트 ──────────────────────────────────────────────

@exam_bp.route("/wrong-answers")
@login_required
def wrong_answers():
    entries = (
        WrongAnswer.query
        .filter_by(user_id=current_user.id)
        .order_by(WrongAnswer.is_mastered, WrongAnswer.added_at.desc())
        .all()
    )
    for e in entries:
        e.options_list = json.loads(e.options) if e.options else []
    unmastered = sum(1 for e in entries if not e.is_mastered)
    return render_template("exam/wrong_answers.html", entries=entries, unmastered=unmastered)


@exam_bp.route("/wrong-answers/quiz")
@login_required
def wrong_answers_quiz():
    entries = (
        WrongAnswer.query
        .filter_by(user_id=current_user.id, is_mastered=False)
        .order_by(WrongAnswer.added_at.desc())
        .all()
    )
    if not entries:
        flash("풀 문제가 없습니다. 오답노트가 비어 있거나 모두 완료했습니다.", "info")
        return redirect(url_for("exam.wrong_answers"))
    for e in entries:
        e.options_list = json.loads(e.options) if e.options else []
    return render_template("exam/wrong_answers_quiz.html", entries=entries)


@exam_bp.route("/wrong-answers/quiz/submit", methods=["POST"])
@login_required
def wrong_answers_quiz_submit():
    entry_ids = request.form.getlist("entry_ids")
    results = []
    mastered_count = 0

    for eid in entry_ids:
        entry = WrongAnswer.query.filter_by(id=int(eid), user_id=current_user.id).first()
        if not entry:
            continue
        user_answer = request.form.get(f"answer_{eid}", "").strip()
        is_correct = _check_answer(entry, user_answer)
        if is_correct:
            entry.is_mastered = True
            mastered_count += 1
        results.append({
            "entry": entry,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "options_list": json.loads(entry.options) if entry.options else [],
        })

    db.session.commit()
    remaining = WrongAnswer.query.filter_by(user_id=current_user.id, is_mastered=False).count()
    return render_template(
        "exam/wrong_answers_result.html",
        results=results, mastered_count=mastered_count, remaining=remaining,
    )


@exam_bp.route("/wrong-answers/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_wrong_answer(entry_id):
    entry = WrongAnswer.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("exam.wrong_answers"))


# ── 시험 삭제 / 채점 헬퍼 ──────────────────────────────────

@exam_bp.route("/exam/<int:exam_id>/delete", methods=["POST"])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    db.session.delete(exam)
    db.session.commit()
    flash("시험이 삭제되었습니다.", "success")
    return redirect(url_for("exam.dashboard"))


def _check_answer(question, user_answer: str) -> bool:
    """Question 또는 WrongAnswer 객체를 모두 처리한다."""
    correct = question.correct_answer.strip()
    if question.question_type == "ox":
        return user_answer.upper() == correct.upper()
    if question.question_type == "multiple_choice":
        return user_answer == correct
    return user_answer.replace(" ", "").lower() == correct.replace(" ", "").lower()
