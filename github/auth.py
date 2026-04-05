"""
GitHub App 인증 모듈
JWT 생성 → Installation Access Token 발급
"""
import json
import re
import subprocess
import time
from pathlib import Path

import jwt
import requests

CONFIG_PATH = Path(__file__).parent.parent / "github_bot.json"


def load_config(path=CONFIG_PATH):
    with open(path) as f:
        return json.load(f)


def generate_jwt(app_id, private_key_path):
    with open(private_key_path, "r") as f:
        private_key = f.read()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 540, "iss": str(app_id)}
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(jwt_token, installation_id):
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    res = requests.post(url, headers=headers)
    res.raise_for_status()
    return res.json()["token"]


def get_owner_repo():
    """git remote origin URL에서 owner와 repo를 파싱해 반환"""
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
        if m:
            return m.group(1), m.group(2)
    except Exception:
        pass
    raise RuntimeError("git remote origin을 파싱할 수 없습니다. origin이 설정되어 있는지 확인하세요.")


def get_token():
    """config를 읽어 installation access token을 반환"""
    config = load_config()
    jwt_token = generate_jwt(config["app_id"], config["private_key_path"])
    return get_installation_token(jwt_token, config["installation_id"])


def make_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
