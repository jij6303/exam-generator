import json
import time
from google import genai
from google.genai.errors import ServerError
from flask import current_app

SYSTEM_PROMPT = """당신은 교육 전문가입니다. 주어진 텍스트를 바탕으로 시험 문제를 생성합니다.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운 코드블록은 포함하지 마세요.

[
  {
    "question_type": "multiple_choice" | "short_answer" | "ox",
    "question_text": "문제 내용",
    "options": ["①보기1", "②보기2", "③보기3", "④보기4"],
    "correct_answer": "정답",
    "explanation": "해설"
  }
]

규칙:
- multiple_choice: options 필드 필수 (4개), correct_answer는 options 중 하나
- short_answer: options 필드 없음
- ox: options 필드 없음, correct_answer는 "O" 또는 "X"
"""


def _dummy_questions(num_multiple_choice: int, num_short_answer: int, num_ox: int) -> list[dict]:
    """API 키 없이 UI 테스트용 더미 문제를 반환한다."""
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
            "explanation": "git stash는 현재 작업 디렉토리의 변경 사항을 임시 저장합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "RESTful API에서 리소스 생성에 사용하는 HTTP 메서드는?",
            "options": ["①GET", "②PUT", "③POST", "④DELETE"],
            "correct_answer": "③POST",
            "explanation": "POST 메서드는 서버에 새로운 리소스를 생성할 때 사용합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Python에서 None 값을 확인하는 올바른 방법은?",
            "options": ["①x == None", "②x is None", "③x === None", "④x != None"],
            "correct_answer": "②x is None",
            "explanation": "None과 같은 싱글턴 객체는 == 대신 is로 비교하는 것이 권장됩니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "CSS에서 요소를 가운데 정렬할 때 사용하는 Flexbox 속성은?",
            "options": ["①align-left: center", "②justify-content: center", "③text-align: flex", "④display: center"],
            "correct_answer": "②justify-content: center",
            "explanation": "justify-content: center는 주축 방향으로 자식 요소를 가운데 정렬합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "JavaScript에서 배열의 마지막 요소를 제거하고 반환하는 메서드는?",
            "options": ["①shift()", "②pop()", "③splice()", "④slice()"],
            "correct_answer": "②pop()",
            "explanation": "pop()은 배열의 마지막 요소를 제거하고 그 값을 반환합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "SQL에서 중복 행을 제거하는 키워드는?",
            "options": ["①UNIQUE", "②DISTINCT", "③FILTER", "④EXCLUDE"],
            "correct_answer": "②DISTINCT",
            "explanation": "SELECT DISTINCT는 결과에서 중복된 행을 제거합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "운영체제에서 프로세스와 스레드의 차이로 옳은 것은?",
            "options": ["①스레드는 독립된 메모리를 가진다", "②프로세스는 메모리를 공유한다", "③스레드는 프로세스 내 실행 단위이다", "④프로세스가 스레드보다 가볍다"],
            "correct_answer": "③스레드는 프로세스 내 실행 단위이다",
            "explanation": "스레드는 프로세스 내에서 실행되는 작업 단위로, 같은 프로세스의 스레드끼리는 메모리를 공유합니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Big-O 표기법에서 가장 빠른 시간 복잡도는?",
            "options": ["①O(n)", "②O(log n)", "③O(1)", "④O(n²)"],
            "correct_answer": "③O(1)",
            "explanation": "O(1)은 상수 시간 복잡도로, 입력 크기에 관계없이 일정한 시간이 소요됩니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "TCP와 UDP의 차이로 옳은 것은?",
            "options": ["①UDP는 연결 지향적이다", "②TCP는 순서를 보장하지 않는다", "③TCP는 신뢰성 있는 전송을 보장한다", "④UDP가 TCP보다 느리다"],
            "correct_answer": "③TCP는 신뢰성 있는 전송을 보장한다",
            "explanation": "TCP는 3-way handshake로 연결을 맺고 데이터 전달을 보장하는 신뢰성 있는 프로토콜입니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Python 데코레이터(@)의 역할로 옳은 것은?",
            "options": ["①변수를 선언한다", "②함수를 감싸 기능을 추가한다", "③클래스를 상속한다", "④예외를 처리한다"],
            "correct_answer": "②함수를 감싸 기능을 추가한다",
            "explanation": "데코레이터는 함수나 클래스를 감싸서 원본 코드 변경 없이 기능을 추가하는 패턴입니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "OOP에서 다형성(Polymorphism)의 의미는?",
            "options": ["①데이터를 숨기는 것", "②하나의 인터페이스로 여러 타입을 다루는 것", "③클래스를 상속받는 것", "④객체를 복사하는 것"],
            "correct_answer": "②하나의 인터페이스로 여러 타입을 다루는 것",
            "explanation": "다형성은 같은 인터페이스나 메서드 이름으로 서로 다른 타입의 객체를 처리할 수 있는 능력입니다.",
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Docker 컨테이너와 가상 머신(VM)의 차이로 옳은 것은?",
            "options": ["①컨테이너는 OS 커널을 포함한다", "②VM이 컨테이너보다 가볍다", "③컨테이너는 호스트 OS 커널을 공유한다", "④Docker는 하이퍼바이저를 사용한다"],
            "correct_answer": "③컨테이너는 호스트 OS 커널을 공유한다",
            "explanation": "Docker 컨테이너는 호스트 OS 커널을 공유하여 VM보다 가볍고 빠르게 실행됩니다.",
        },
    ]
    sa_pool = [
        {
            "question_type": "short_answer",
            "question_text": "Python에서 딕셔너리의 모든 키를 반환하는 메서드는?",
            "options": None,
            "correct_answer": "keys()",
            "explanation": "dict.keys()는 딕셔너리의 모든 키를 반환합니다.",
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
            "question_text": "소프트웨어 개발에서 가장 널리 사용되는 분산 버전 관리 시스템은?",
            "options": None,
            "correct_answer": "Git",
            "explanation": "Git은 현재 가장 널리 사용되는 분산 버전 관리 시스템입니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "HTTP에서 클라이언트가 서버에 데이터를 전송할 때 주로 사용하는 메서드는?",
            "options": None,
            "correct_answer": "POST",
            "explanation": "POST 메서드는 요청 본문(body)에 데이터를 담아 서버로 전송합니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "Python에서 리스트 컴프리헨션으로 1~10의 짝수 리스트를 만드는 식은?",
            "options": None,
            "correct_answer": "[x for x in range(1, 11) if x % 2 == 0]",
            "explanation": "리스트 컴프리헨션은 [표현식 for 변수 in 반복가능객체 if 조건] 형태입니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "관계형 DB에서 두 테이블을 공통 컬럼으로 합치는 SQL 명령어는?",
            "options": None,
            "correct_answer": "JOIN",
            "explanation": "JOIN은 두 테이블을 공통된 키 값을 기준으로 결합합니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "CSS에서 박스 모델의 구성 요소 4가지를 나열하시오.",
            "options": None,
            "correct_answer": "content, padding, border, margin",
            "explanation": "CSS 박스 모델은 content(내용), padding(안쪽 여백), border(테두리), margin(바깥 여백)으로 구성됩니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "네트워크에서 도메인 이름을 IP 주소로 변환하는 시스템은?",
            "options": None,
            "correct_answer": "DNS",
            "explanation": "DNS(Domain Name System)는 사람이 읽을 수 있는 도메인을 IP 주소로 변환합니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "Python에서 예외를 처리하는 구문은?",
            "options": None,
            "correct_answer": "try-except",
            "explanation": "try 블록에서 예외가 발생하면 except 블록이 실행됩니다.",
        },
        {
            "question_type": "short_answer",
            "question_text": "CI/CD에서 CI가 의미하는 것은?",
            "options": None,
            "correct_answer": "Continuous Integration",
            "explanation": "CI(지속적 통합)는 코드 변경 사항을 자주 병합하고 자동으로 빌드·테스트하는 개발 방식입니다.",
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
            "explanation": "HTTP는 stateless 프로토콜로, 각 요청은 독립적입니다.",
        },
        {
            "question_type": "ox",
            "question_text": "Git에서 git pull은 fetch와 merge를 합친 동작이다.",
            "options": None,
            "correct_answer": "O",
            "explanation": "git pull = git fetch + git merge로, 원격 변경 사항을 가져와 현재 브랜치에 병합합니다.",
        },
        {
            "question_type": "ox",
            "question_text": "SQL의 WHERE 절은 GROUP BY 이후에 실행된다.",
            "options": None,
            "correct_answer": "X",
            "explanation": "실행 순서는 FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY 입니다.",
        },
        {
            "question_type": "ox",
            "question_text": "HTTPS는 SSL/TLS를 사용해 데이터를 암호화한다.",
            "options": None,
            "correct_answer": "O",
            "explanation": "HTTPS는 SSL/TLS 프로토콜로 통신을 암호화하여 보안을 강화합니다.",
        },
        {
            "question_type": "ox",
            "question_text": "Python의 리스트(list)는 불변(immutable) 자료형이다.",
            "options": None,
            "correct_answer": "X",
            "explanation": "Python 리스트는 가변(mutable) 자료형입니다. 불변 자료형은 tuple입니다.",
        },
        {
            "question_type": "ox",
            "question_text": "REST API에서 GET 요청은 서버의 상태를 변경하지 않아야 한다.",
            "options": None,
            "correct_answer": "O",
            "explanation": "GET은 멱등성(idempotent)을 가져야 하며 서버 상태를 변경하지 않는 조회 전용 메서드입니다.",
        },
        {
            "question_type": "ox",
            "question_text": "Docker 이미지는 컨테이너를 실행한 후 수정할 수 있다.",
            "options": None,
            "correct_answer": "X",
            "explanation": "Docker 이미지는 읽기 전용(read-only)입니다. 컨테이너 실행 시 쓰기 가능한 레이어가 별도로 추가됩니다.",
        },
        {
            "question_type": "ox",
            "question_text": "IPv6 주소는 128비트로 구성된다.",
            "options": None,
            "correct_answer": "O",
            "explanation": "IPv6는 128비트 주소 체계를 사용하며, IPv4(32비트)보다 훨씬 많은 주소를 제공합니다.",
        },
        {
            "question_type": "ox",
            "question_text": "OOP에서 캡슐화(Encapsulation)는 상속을 의미한다.",
            "options": None,
            "correct_answer": "X",
            "explanation": "캡슐화는 데이터와 메서드를 하나로 묶고 내부 구현을 숨기는 것입니다. 상속은 별개의 개념입니다.",
        },
    ]

    return mc_pool[:num_multiple_choice] + sa_pool[:num_short_answer] + ox_pool[:num_ox]


def generate_questions(
    text: str,
    num_multiple_choice: int = 5,
    num_short_answer: int = 3,
    num_ox: int = 2,
) -> list[dict]:
    """Gemini API로 문제를 생성한다. API 키가 없으면 더미 문제를 반환한다."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return _dummy_questions(num_multiple_choice, num_short_answer, num_ox)

    client = genai.Client(api_key=api_key)

    prompt = f"""{SYSTEM_PROMPT}

아래 텍스트를 읽고 다음 문제를 생성하세요:
- 객관식(4지선다) {num_multiple_choice}문제
- 단답형 {num_short_answer}문제
- OX 문제 {num_ox}문제

텍스트:
{text[:8000]}"""

    last_error = None
    for attempt in range(4):  # 최초 1회 + 재시도 3회
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            last_error = None
            break
        except ServerError as e:
            if e.code != 503:
                raise
            last_error = e
            if attempt < 3:
                time.sleep(2)

    if last_error is not None:
        raise last_error

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
