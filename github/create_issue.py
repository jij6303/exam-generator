"""
이슈 생성 스크립트

단독 실행:
    python create_issue.py --title "제목" --body "내용"

모듈 사용:
    from github.create_issue import create_issue
    issue_number = create_issue(token, owner, repo, title, body)
"""
import argparse

import requests

from auth import get_owner_repo, get_token, make_headers


def create_issue(token, owner, repo, title, body=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    res = requests.post(url, headers=make_headers(token), json={"title": title, "body": body})
    res.raise_for_status()
    issue = res.json()
    print(f"이슈 생성 완료: #{issue['number']} {issue['title']}")
    print(f"URL: {issue['html_url']}")
    return issue["number"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub 이슈 생성")
    parser.add_argument("--title", required=True, help="이슈 제목")
    parser.add_argument("--body", default="", help="이슈 본문")
    args = parser.parse_args()

    owner, repo = get_owner_repo()
    token = get_token()
    create_issue(token, owner, repo, args.title, args.body)
