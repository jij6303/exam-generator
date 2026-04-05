"""
리뷰 요청 스크립트

단독 실행:
    python request_review.py --pr 1 --reviewers user1
    python request_review.py --pr 1 --reviewers user1 user2 user3

모듈 사용:
    from github.request_review import request_review
    request_review(token, owner, repo, pr_number, reviewers)
"""
import argparse

import requests

from auth import get_owner_repo, get_token, make_headers


def request_review(token, owner, repo, pr_number, reviewers):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
    res = requests.post(url, headers=make_headers(token), json={"reviewers": reviewers})
    res.raise_for_status()
    print(f"리뷰 요청 완료: PR #{pr_number} → {', '.join(reviewers)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub PR 리뷰 요청")
    parser.add_argument("--pr", required=True, type=int, help="PR 번호")
    parser.add_argument("--reviewers", required=True, nargs="+", help="리뷰어 GitHub 유저명 (공백으로 구분)")
    args = parser.parse_args()

    owner, repo = get_owner_repo()
    token = get_token()
    request_review(token, owner, repo, args.pr, args.reviewers)
