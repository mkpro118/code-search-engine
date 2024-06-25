import collections
import dataclasses
import functools
import logging
import pathlib
import posixpath

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Collection, Optional

from gh_api import get_request
from gh_api.blob import Blob

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()


class DownloadCallback:
    def __call__(self, blob: Blob) -> None:
        self.downloader(blob)

    def __init__(self, root: str | pathlib.Path,
                 makedirs: bool = False,
                 overwrite: bool = False):
        self.downloader = functools.partial(
            Blob.download,
            root=root,
            makedirs=makedirs,
            overwrite=overwrite,
        )


@dataclasses.dataclass
class Repository:
    user: str
    name: str
    url: str
    tree: Optional[list[dict[str, str]]] = None
    blobs: Optional[tuple[Blob, ...]] = None

    def __hash__(self):
        return hash(self.name)

    def get_tree(self, ref_or_sha: str = 'main',
                 recursive: bool = True) -> list[dict[str, str]]:
        if self.tree is not None:
            log.info(f'Already downloaded tree for {self.name}. Using cache')
            return self.tree

        log.info(f'Tree cache not available for {self.name}. '
                 f'Downloading from {self.url}')

        url = posixpath.join(self.url, 'git', 'trees', ref_or_sha)
        if recursive:
            url += '?recursive=true'

        data = get_request(url=url)

        self.tree = data['tree']
        return self.tree

    def get_blobs(self) -> tuple[Blob, ...]:
        if self.blobs is not None:
            log.info(f'Already downloaded blobs for {self.name}. Using cache')
            return self.blobs
        repo_tree = self.get_tree(recursive=True)

        filtered = filter(lambda x: x['type'] == 'blob', repo_tree)
        del_type = map(lambda x: (x.pop('type') and None) or x, filtered)
        blobs = map(lambda x: Blob(**x), del_type)  # type: ignore[arg-type]

        self.blobs = tuple(blobs)

        return self.blobs

    def download_blobs(self, root: str | pathlib.Path,
                       makedirs: bool = False,
                       overwrite: bool = False,
                       use_threads: bool = False,
                       max_threads: Optional[int] = None) -> None:
        blobs = self.get_blobs()

        downloader = DownloadCallback(root=root,
                                      makedirs=makedirs,
                                      overwrite=overwrite)

        download_strategy: Callable[[DownloadCallback, Collection[Blob]], None]

        if use_threads or isinstance(max_threads, int):
            download_strategy = functools.partial(
                Repository.parallel_download,
                max_threads=max_threads
            )
        else:
            download_strategy = Repository.sequential_download

        download_strategy(downloader, blobs)

    @staticmethod
    def sequential_download(downloader: DownloadCallback,
                            blobs: Collection[Blob]) -> None:
        log.info(f'Sequential downloading for {len(blobs)} blobs')
        mapper = map(downloader, blobs)
        collections.deque(mapper, maxlen=0)
        log.info('Download Complete!')

    @staticmethod
    def parallel_download(downloader: DownloadCallback,
                          blobs: Collection[Blob],
                          max_threads: Optional[int] = None) -> None:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(downloader, blobs)
        log.info('Download Complete!')

    @classmethod
    def get_repositories(cls, user: str) -> list['Repository']:
        url = posixpath.join('https://api.github.com/users', user, 'repos')
        data = get_request(url=url)
        repos: list[Repository] = [
            cls(
                user=user,
                name=item['name'],
                url=item['url']
            ) for item in data
        ]

        return repos
