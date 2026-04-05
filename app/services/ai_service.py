import json
import anthropic
from flask import current_app

SYSTEM_PROMPT = """당신은 교육 전문가입니다. 주어진 텍스트를 바탕으로 시험 문제를 생성합니다.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

[
  {
    "question_type": "multiple_choice" | "short_answer" | "ox",
    "question_text": "문제 내용",
    "options": ["①보기1", "②보기2", "③보기3", "④보기4"],  // 객관식만 포함
    "correct_answer": "정답",
    "explanation": "해설"
  }
]"""


def _dummy_questions(num_multiple_choice: int, num_short_answer: int, num_ox: int) -> list[dict]:
    """API 키 없이 UI 테스트용 더미 문제를 반환한다."""
    questions = []

    mc_pool = [
        {
            "question_type": "multiple_choice",
            "question_text": "Python에서 리스트를 정렬하는 내장 메서드는?",
            "options": ["①sort()", "②order()", "③arrange()", "④rank()"],
            "correct_answer": "①sort()",
            "explanation": "list.sort()는 리스트를 제자리(in-place)에서 정렬합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "HTTP 상태 코드 404의 의미는?",
            "options": ["①서버 오류", "②요청 성공", "③리소스를 찾을 수 없음", "④권한 없음"],
            "correct_answer": "③리소스를 찾을 수 없음",
            "explanation": "404 Not Found는 요청한 리소스가 서버에 존재하지 않을 때 반환됩니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "관계형 데이터베이스에서 기본 키(Primary Key)의 특징은?",
            "options": ["①중복 허용", "②NULL 허용", "③유일하고 NULL 불가", "④외래 키와 동일"],
            "correct_answer": "③유일하고 NULL 불가",
            "explanation": "기본 키는 테이블의 각 행을 고유하게 식별하며 NULL 값을 가질 수 없습니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Git에서 변경 사항을 임시 저장하는 명령어는?",
            "options": ["①git save", "②git stash", "③git hold", "④git temp"],
            "correct_answer": "②git stash",
            "explanation": "git stash는 현재 작업 디렉토리의 변경 사항을 임시 저장하고 워킹 디렉토리를 깨끗하게 만듭니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "RESTful API에서 리소스 생성에 사용하는 HTTP 메서드는?",
            "options": ["①GET", "②PUT", "③POST", "④DELETE"],
            "correct_answer": "③POST",
            "explanation": "POST 메서드는 서버에 새로운 리소스를 생성할 때 사용합니다.",
        },
    ]

    sa_pool = [
        {
            "question_type": "short_answer",
            "question_text": "Python에서 딕셔너리의 모든 키를 반환하는 메서드는?",
            "options": None,
            "correct_answer": "keys()",
            "explanation": "dict.keys()는 딕셔너리의 모든 키를 dict_keys 객체로 반환합니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "HTML에서 하이퍼링크를 만드는 태그는?",
            "options": None,
            "correct_answer": "<a>",
            "explanation": "<a> (anchor) 태그는 href 속성과 함께 하이퍼링크를 정의합니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "소프트웨어 개발에서 버전 관리 시스템(VCS)의 대표적인 예는?",
            "options": None,
            "correct_answer": "Git",
            "explanation": "Git은 현재 가장 널리 사용되는 분산 버전 관리 시스템입니다.",
        },
    ]

    ox_pool = [
        {
            "question_type": "ox",
            "question_text": "Python은 인터프리터 언어이다.",
            "options": None,
            "correct_answer": "O",
            "explanation": "Python은 소스 코드를 한 줄씩 해석하는 인터프리터 언어입니다.",
        },
        {
            "question_type": "ox",
            "question_text": "HTTP는 상태를 유지하는(stateful) 프로토콜이다.",
            "options": None,
            "correct_answer": "X",
            "explanation": "HTTP는 stateless 프로토콜로, 각 요청은 독립적이며 이전 요청 정보를 기억하지 않습니다.",
        },
    ]

    questions += mc_pool[:num_multiple_choice]
    questions += sa_pool[:num_short_answer]
    questions += ox_pool[:num_ox]
    return questions


def generate_questions(
    text: str,
    num_multiple_choice: int = 5,
    num_short_answer: int = 3,
    num_ox: int = 2,
) -> list[dict]:
    """Claude AI를 사용해 문제를 생성한다. API 키가 없으면 더미 문제를 반환한다."""
    api_key = current_app.config.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _dummy_questions(num_multiple_choice, num_short_answer, num_ox)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""아래 텍스트를 읽고 다음 문제를 생성하세요:
- 객관식(4지선다) {num_multiple_choice}문제
- 단답형 {num_short_answer}문제
- OX 문제 {num_ox}문제

텍스트:
{text[:8000]}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
