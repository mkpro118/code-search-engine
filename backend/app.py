import threading
import time
import flask
import logging

from concurrent.futures import ThreadPoolExecutor

from repository import Repository

app = flask.Flask(__name__)


def init_db(db_uri: str) -> None:
    pass


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

done: dict[str, str] = {}


def download_single(repo: Repository) -> None:
    while repo.name != 'ArrowQuest':
        try:
            repo.download_blobs(
                root=f'gh_data/repos/{repo.user}/{repo.name}',
                makedirs=True,
                use_threads=True,
                overwrite=True
            )
            done[repo.name] = 'Complete'
            break
        except Exception:
            _, n = done[repo.name].split(' ')
            done[repo.name] = f'Attempt {int(n) + 1}'
            log.critical(f'{repo.name = } waiting for an hour')
            time.sleep(3600)  # Try again in 1 hour


def download(user: str) -> None:
    global done
    repos = Repository.get_repositories(user)
    log.info(
        'Found Repositories:\n'
        '\n'.join(map(str, repos))
    )

    done = {r.name: 'Attempt 1' for r in repos}

    with ThreadPoolExecutor() as executor:
        executor.map(download_single, repos)


@app.route('/')
def home() -> str:
    return '<div>Welcome to app! Glad to see you here</div>'


@app.route('/download/<name>')
def function(name: str) -> 'str':
    thread = threading.Thread(target=download, args=(name,))
    thread.start()
    if len(done) == 0:
        return f'Started downloads for {name}'
    else:
        resp = '\n'.join(map(lambda x: f'<li>{x}</li>', done.items()))
        return f'<ul>{resp}</ul>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
