"""
브랜치 생성 스크립트

단독 실행:
    python create_branch.py --branch feature-#N
    python create_branch.py --branch feature-#N --base develop

모듈 사용:
    from github.create_branch import create_branch
    create_branch(token, owner, repo, branch_name, base_branch)
"""
import argparse

import requests

from auth import get_owner_repo, get_token, make_headers


def create_branch(token, owner, repo, branch_name, base_branch="main"):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
    res = requests.get(url, headers=make_headers(token))
    res.raise_for_status()
    sha = res.json()["object"]["sha"]

    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    res = requests.post(
        url,
        headers=make_headers(token),
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
    )
    res.raise_for_status()
    print(f"브랜치 생성 완료: {branch_name} (base: {base_branch}, sha: {sha[:7]})")
    return sha


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub 브랜치 생성")
    parser.add_argument("--branch", required=True, help="생성할 브랜치 이름")
    parser.add_argument("--base", default="main", help="기준 브랜치 (기본값: main)")
    args = parser.parse_args()

    owner, repo = get_owner_repo()
    token = get_token()
    create_branch(token, owner, repo, args.branch, args.base)
