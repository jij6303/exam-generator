# 작업 규칙

## 중요: GitHub 작업은 반드시 github_bot.py를 사용할 것

이 레포에서 이슈 생성, 브랜치 생성, PR 생성, 리뷰 요청 등 **모든 GitHub 작업**은
`github/` 모듈을 통해 수행해야 한다.

- `gh` CLI, 직접 `git push` 후 수동 PR 생성 등은 사용하지 않는다.
- 작업 전 `github_bot.json`이 올바르게 설정되어 있어야 한다.

### github_bot.json 설정 (최초 1회)

```json
{
  "app_id": <GitHub App ID>,
  "installation_id": <Installation ID>,
  "private_key_path": "<private key .pem 파일 절대 경로>",
  "owner": "<GitHub 유저명 또는 org>",
  "repo": "<레포지토리 이름>"
}
```

> `github_bot.json.example`을 복사해서 `github_bot.json`으로 만들고 값을 채운다.
> `github_bot.json`은 `.gitignore`에 추가해 커밋하지 않는다.

### 봇 사용 방법

```bash
# 이슈 생성
python github/create_issue.py --title "제목" --body "내용"

# 브랜치 생성
python github/create_branch.py --branch feature-#N

# PR 생성
python github/create_pr.py --title "feat(#N): description" --head feature-#N --body "Closes #N\n\n내용"

# 리뷰 요청
python github/request_review.py --pr N --reviewers username
```

---

## 워크플로우

작업 시작 전 반드시 아래 순서를 따른다.

1. `main` 브랜치에서 최신 코드 pull
2. 이슈 생성 — `github/create_issue.py` 사용, 제목·본문 **한글**
3. 브랜치 생성 — `github/create_branch.py` 사용 (`feature-#N`)
4. 로컬에서 브랜치 체크아웃
5. 이슈에 개발 계획 코멘트 작성 (한글, GitHub API 직접 또는 봇 활용)
6. 개발
7. PR 생성 — `github/create_pr.py` 사용
8. 리뷰 요청 — `github/request_review.py` 사용

---

## Git 컨벤션

### 브랜치
```
feature-#<이슈번호>
```

### 커밋 메시지 (영어)
```
type(#N): description
```

| 타입 | 용도 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `refactor` | 리팩토링 |
| `docs` | 문서 |
| `chore` | 설정·정리 |

규칙: 소문자, 마침표 없음, 이슈 번호 필수

### PR
- 제목: **영어** — `type(#N): description`
- 본문: **한글**, 첫 줄에 `Closes #N` 포함
- base: `main`

---

## 예시

```
이슈:    #5 로그인 기능 구현
브랜치:  feature-#5
커밋:    feat(#5): add login API
PR 제목: feat(#5): add login API
PR 본문: Closes #5
         로그인 API 및 세션 처리 구현
```
