import dotenv
import logging
import os
import pathlib
import requests

from typing import Any

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()

dotenv.load_dotenv()
secrets_path = '/run/secrets/gh_secret'
if pathlib.Path().resolve().is_file():
    dotenv.load_dotenv('/run/secrets/gh_secret')

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if 'GITHUB_PAT' in os.environ:
    log.info('Found $GITHUB_PAT')
    HEADERS["Authorization"] = f"Bearer {os.environ.get('GITHUB_PAT')}"


def get_request(url: str, headers: dict[str, str] = HEADERS) -> Any:
    with requests.get(url=url, headers=headers) as resp:
        resp.raise_for_status()
        rate_limit_remaining = resp.headers.get('x-ratelimit-remaining',
                                                'No Rate Limit found')
        log.info(f'{rate_limit_remaining = }')
        return resp.json()
