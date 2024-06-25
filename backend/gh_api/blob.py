import base64
import dataclasses
import logging
import pathlib

from typing import Optional

from gh_api import get_request

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()


@dataclasses.dataclass
class Blob:
    mode: str
    path: str
    sha: str
    size: int
    url: str
    content: Optional[str] = None

    def get_contents(self) -> str:
        if self.content is not None:
            log.info(f'Already downloaded {self.path}. Using cached content')
            return self.content

        log.info(
            f'Cache not available for {self.path}. '
            'Downloading from {self.url}'
        )

        data = get_request(url=self.url)
        content = data['content']  # Cache contents
        self.content = base64.b64decode(content).decode('utf-8')
        return self.content

    def download(self, root: str | pathlib.Path,
                 makedirs: bool = False, overwrite: bool = False) -> None:
        if self.path.endswith('jpg') or self.path.endswith('jpeg') or self.path.endswith('png'):
            return

        log.info(f'Downloading... {self.path}')

        content = self.get_contents()

        if not isinstance(root, pathlib.Path):
            root = pathlib.Path(root).resolve()

        if not root.is_dir():
            msg = f'{root = } is not a directory.'
            if makedirs:
                msg += ' Creating is because makedirs is True'
                log.info(msg)
                root.mkdir(parents=True, exist_ok=True)
            else:
                log.error(msg)
                raise ValueError(msg)

        filepath = root / self.path
        filepath = filepath.resolve()

        if filepath.exists():
            if filepath.is_file() and not overwrite:
                msg = (
                    f'{filepath} exists, and would be overwritten. '
                    'Specify `overwrite=True` if this is intended'
                )
                log.error(msg)
                raise ValueError(msg)
            if overwrite:
                if not filepath.is_file():
                    msg = (
                        f'{filepath} exists, but it is not a regular file. '
                        'Cannot overwrite'
                    )
                    log.error(msg)
                    raise ValueError(msg)
                log.warning(f'{filepath} exists, overwriting')

        if not filepath.parent.exists():
            msg = (
                f"Output file's parent directory "
                f"{filepath.parent} does not exist."
            )

            if makedirs:
                msg += ' Creating is because makedirs is True'
                log.info(msg)
                filepath.parent.mkdir(exist_ok=True, parents=True)
            else:
                msg += (
                    ' Cannot create file. Specify `makedirs=True` to '
                    'make all necessary directories'
                )

                log.info(msg)
                raise ValueError(msg)
        filepath_str = str(filepath)

        log.info(f'Writing {self.size} bytes to {filepath_str}')
        with open(filepath_str, 'w') as f:
            f.write(content)
