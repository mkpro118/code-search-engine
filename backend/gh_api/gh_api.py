import dotenv
import logging
import os
import pathlib
import requests
import urllib

from collections import namedtuple
from typing import Any

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()

dotenv.load_dotenv()
secrets_path = "/run/secrets/gh_secret"
if pathlib.Path().resolve().is_file():
    dotenv.load_dotenv("/run/secrets/gh_secret")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

GH_URL_Components = namedtuple(  # type: ignore[misc]
    typename="GH_URL_Components",
    field_names=["scheme", "netloc", "path", "params", "query", "fragment"],
)

if "GITHUB_PAT" in os.environ:
    log.info("Found $GITHUB_PAT")
    HEADERS["Authorization"] = f"Bearer {os.environ.get('GITHUB_PAT')}"


def get_request(url: str, headers: dict[str, str] = HEADERS) -> Any:
    with requests.get(url=url, headers=headers) as resp:
        resp.raise_for_status()
        rate_limit_remaining = resp.headers.get(
            "x-ratelimit-remaining", "No Rate Limit found"
        )
        log.info(f"{rate_limit_remaining = }")
        return resp.json()


def to_gh_url(user: str, repo: str, filepath: str | pathlib.Path) -> str:
    components = GH_URL_Components(  # type: ignore[call-arg]
        scheme="https",
        netloc="github.com",
        path=urllib.parse.quote(f"{user}/{repo}/blob/main/{filepath}"),
        params=None,
        query=None,
        fragment=None,
    )
    return str(urllib.parse.urlunparse(components))
