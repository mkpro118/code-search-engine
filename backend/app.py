import flask
import logging
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from flask import request
from flask_cors import CORS

from gh_api.repository import Repository
from snippets.languages import Language

app = flask.Flask(__name__)
CORS(app)


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

done: dict[str, str] = {}


def download_single(repo: Repository) -> None:
    while repo.name != "ArrowQuest":
        try:
            repo.download_blobs(
                root=f"gh_data/repos/{repo.user}/{repo.name}",
                makedirs=True,
                use_threads=True,
                overwrite=True,
            )
            done[repo.name] = "Complete"
            break
        except Exception:
            _, n = done[repo.name].split(" ")
            done[repo.name] = f"Attempt {int(n) + 1}"
            log.critical(f"{repo.name = } waiting for an hour")
            time.sleep(3600)  # Try again in 1 hour


def download(user: str) -> None:
    global done
    repos = Repository.get_repositories(user)
    log.info("Found Repositories:\n" "\n".join(map(str, repos)))

    done = {r.name: "Attempt 1" for r in repos}

    with ThreadPoolExecutor() as executor:
        executor.map(download_single, repos)


@app.route("/")
def home() -> str:
    return "<div>Welcome to app! Glad to see you here</div>"


@app.route("/download/<name>")
def get_repos(name: str) -> "str":
    thread = threading.Thread(target=download, args=(name,))
    thread.start()
    if len(done) == 0:
        return f"Started downloads for {name}"
    else:
        resp = "\n".join(map(lambda x: f"<li>{x}</li>", done.items()))
        return f"<ul>{resp}</ul>"


@app.route("/chat", methods=["GET", "POST"])
def chat():
    params = request.json
    print(f"{params = }", flush=True)
    return {"answer": "Hi How can I help?"}


@app.route("/langs", methods=["GET"])
def langs() -> list[dict[str, str]]:
    langs: list[dict[str, str]] = []

    for key, value in Language._member_map_.items():
        langs.append({"name": key, "description": value.value})

    return langs


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
