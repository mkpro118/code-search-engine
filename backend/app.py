import flask
import functools
import json
import logging
import os
import pathlib
import signal
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from flask import request, Response
from flask_cors import CORS
from typing import cast, Any

import gh_api
from gh_api.repository import Repository
from snippets.languages import Language
from search_engine import CodeSearchEngine, too_big, is_not_supported

app = flask.Flask(__name__)
CORS(app)

REPO_ROOT = pathlib.Path('/app/gh_data/repos')
INDEX_FILE = pathlib.Path('/app/indexes/indexes.json')

engines: dict[tuple[str, str], CodeSearchEngine] = dict()
# user: str = 'mkpro118'
# repo: str = 'mkpro118-repository'
# engines[(user, repo)] = CodeSearchEngine(user, repo)
# engines[(user, repo)].train(
#     exclude_dir_if=too_big,
#     exclude_file_if=is_not_supported,
#     pretrained_ok=True
# )

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

done: dict[str, str] = {}


def save_indexes(
    *args: tuple[Any, ...],
    filepath: pathlib.Path = INDEX_FILE,
    **kwargs: dict[Any, Any],
) -> None:
    indexes: list[dict[str, str]] = []
    for key in engines.keys():
        indexes.append({'user': key[0], 'repo': key[1]})

    with open(str(filepath), 'w') as f:
        json.dump(indexes, f)


signal.signal(signal.SIGTERM, save_indexes)  # type: ignore[arg-type]


def load_indexes(filepath: pathlib.Path = INDEX_FILE) -> None:
    global engines
    if not filepath.is_file():
        print('No indexes to load')
        return

    try:
        with open(str(filepath)) as f:
            indexes = json.load(f)
    except json.decoder.JSONDecodeError:
        print('Failed to load indexes skipping')
        return

    for index in indexes:
        user, repo = index['user'], index['repo']
        engines[(user, repo)] = CodeSearchEngine(user=user, repo=repo)
        print(f'Found index {(user, repo)}')

    def _load_train(engine: CodeSearchEngine) -> None:
        print(f'Training {engine.user}/{engine.repo}', flush=True)
        engine.train(
            exclude_dir_if=too_big,
            exclude_file_if=is_not_supported,
            pretrained_ok=True,
        )

    with ThreadPoolExecutor() as executor:
        executor.map(_load_train, engines.values())


def download_single(repo: Repository) -> None:
    root = str((REPO_ROOT / repo.user / repo.name).resolve())
    while repo.name != "ArrowQuest":
        try:
            repo.download_blobs(
                root=root,
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


@app.route("/download")
def get_repos() -> "str":
    params = request.json
    print(params)
    assert params is not None, 'No JSON Body'
    print(f"{params = }", flush=True)
    user = params.get('user', None)
    assert user is not None, 'User is none'
    thread = threading.Thread(target=download, args=(user,))
    thread.start()
    if len(done) == 0:
        return f"Started downloads for {user}"
    else:
        resp = "\n".join(map(lambda x: f"<li>{x}</li>", done.items()))
        return f"<ul>{resp}</ul>"


@app.route('/train', methods=['POST'])
def train() -> dict[str, str] | Response:
    params = request.json
    assert params is not None, 'No JSON Body'
    print(f"{params = }", flush=True)
    user = params.get('user', None)
    repo = params.get('repo', None)

    if not (REPO_ROOT / user / repo).is_dir():
        return Response(
            f'We do not have the repositories for {user=}'
            f'You can initiate a download for it by sending a POST request '
            f'to "/download" with JSON body as {{"user": {user}}}',
            status=404,
        )

    index = (user, repo)
    if index not in engines:
        engines[index] = CodeSearchEngine(user=user, repo=repo)

    def re_train(engine: CodeSearchEngine) -> None:
        engine.train(
            exclude_dir_if=too_big,
            exclude_file_if=is_not_supported,
            retrain=True,
        )
        save_indexes()

    thread = threading.Thread(target=re_train, args=(engines[index],))
    thread.start()

    return {
        'message': (
            'Training has started, and will be complete shortly. '
            'Actual training time depends on the size of the repository. '
            'You can check whether the engine is done training by sending a'
            ' POST request to "/is_trained" and using the index from this '
            'response in JSON body as {"index": index}. '
            'The response from that request will have a key "trained" with '
            'a boolean value, true implies engine is trained, false otherwise.'
        ),
        'index': os.path.join(*index),
    }


@app.route("/is_trained", methods=["POST"])
def is_trained() -> dict[str, str | bool] | Response:
    params = request.json
    assert params is not None
    print(f"{params = }", flush=True)
    index = params.get('index', None)

    if index is None:
        return Response(f'{index = } Not Found', status=404)

    index_t: tuple[str, ...] = tuple(index.split('/'))
    print(f'{index_t = }')

    if len(index_t) != 2:
        return Response(f'{index = } is not a valid index', status=404)

    if index_t not in engines:
        return Response(f'{index = } Not Found', status=404)

    return {'index': index, 'trained': engines[index_t].is_trained()}


@app.route("/search", methods=["POST"])
def search() -> list[dict[str, str]] | Response:
    params = request.json
    assert params is not None
    print(f"{params = }", flush=True)
    user = params.get('user', None)
    repo = params.get('repo', None)
    query = params.get('query', None)
    language = params.get('language', None)
    limit = params.get('limit', 5)

    if user is None or repo is None:
        return Response(f'Must have user/repo, found {user}/{repo}', status=404)
    if query is None:
        return Response(f'Must have a query', status=400)

    results = engines[(user, repo)].search(
        query=query, language=language, limit=limit
    )
    print(results.columns.to_list())
    return_set = {'text', 'language', 'filename'}
    filtered = [c for c in results.columns.to_list() if c not in return_set]
    if filtered:
        results.drop(columns=filtered, inplace=True)
    results.drop_duplicates('filename', inplace=True)
    results['text'] = [
        '\n'.join(map(lambda x: x.rstrip(), text.splitlines()[:5]))
        for text in results['text']
    ]

    file_url = functools.partial(gh_api.to_gh_url, user, repo)
    user_root = REPO_ROOT / user / repo

    def relpath(path: str) -> str:
        return str(pathlib.Path(path).relative_to(user_root))

    def name_only(path: str) -> str:
        return pathlib.Path(path).name

    results['link'] = [file_url(relpath(file)) for file in results['filename']]
    results['filename'] = [name_only(file) for file in results['filename']]

    # Mypy could not infer type
    return cast(list[dict[str, str]], results.to_dict('records'))


@app.route("/langs", methods=["GET"])
def langs() -> list[dict[str, str]]:
    langs: list[dict[str, str]] = []

    for key, value in Language._member_map_.items():
        langs.append({"name": key, "description": value.value})

    return langs


if __name__ == "__main__":
    import warnings

    warnings.simplefilter('once')
    load_indexes()
    save_indexes()
    app.run(host="0.0.0.0", port=5000, debug=True)
