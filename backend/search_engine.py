import os
import pathlib

import pandas as pd
from typing import Callable, Generator, Iterable, Optional

from lancedb.rerankers import Reranker

from snippets import Snippet
from snippets.languages import Language
from snippets.lancedb.config import DBConfig, ST_Config
from snippets.lancedb.db_connection import SnippetDBConnection
from snippets.lancedb.table import SnippetTable
from snippets.lancedb.generator import SnippetGenerator


def _return_false(_: str) -> bool:
    return False


def get_snippets(
    root: str | pathlib.Path,
    exclude_dir_if: Optional[Callable[[str], bool]] = None,
    exclude_file_if: Optional[Callable[[str], bool]] = None,
) -> Generator[Snippet, None, None]:
    exclude_dir_if = exclude_dir_if or _return_false
    exclude_file_if = exclude_file_if or _return_false

    for root, dirs, files in os.walk(str(root)):
        dirs[:] = [d for d in dirs if not exclude_dir_if(d)]

        for file in files:
            if exclude_file_if(file):
                continue

            fp = pathlib.Path(root) / file
            yield Snippet.from_file(fp)


def too_big(path: str) -> bool:
    return any(
        (
            path == ".git",
            path == ".mypy_cache",
            path == "CS-539-project",
            path == "neural_network",
        )
    )


def is_not_supported(path: str) -> bool:
    try:
        Language.from_file_extension(path)
        return False
    except ValueError:
        return True


class CodeSearchEngine:
    DB_ROOT: str = 'cse_db'
    DATA_ROOT: str = os.path.join('gh_data', 'repos')

    def __init__(
        self,
        user: str,
        repo: str,
        use_config: Optional[DBConfig] = None,
        use_db_uri: Optional[str] = None,
        use_db: Optional[SnippetDBConnection] = None,
        use_table_name: Optional[str] = None,
        use_table: Optional[SnippetTable] = None,
        use_generator: Optional[SnippetGenerator] = None,
    ):
        self.user = user
        self.repo = repo
        self.config = use_config or ST_Config()
        self.db_uri = use_db_uri or os.path.join(CodeSearchEngine.DB_ROOT, user)
        self.db = use_db or SnippetDBConnection.from_uri(
            self.config, self.db_uri
        )
        self.table_name = use_table_name or self.repo
        self.table = use_table or self.db.get_or_create_table(
            self.config, self.table_name
        )
        self.generator = use_generator or SnippetGenerator(table=self.table)

    def train(
        self,
        repo: Optional[str | pathlib.Path] = None,
        exclude_dir_if: Optional[Callable[[str], bool]] = None,
        exclude_file_if: Optional[Callable[[str], bool]] = None,
        retrain: bool = False,
        pretrained_ok: bool = False,
    ) -> bool:  # Retval is whether or not the engine was trained
        if repo is None:
            repo = os.path.join(
                CodeSearchEngine.DATA_ROOT, self.user, self.repo
            )

        if self.is_trained():
            if pretrained_ok:
                return False
            if not retrain:
                raise ValueError(
                    f'Engine is already trained on {repo}. '
                    f'Use `retrain=True` to retrain the engine.'
                )

        if not isinstance(repo, pathlib.Path):
            repo = pathlib.Path(repo)

        repo = repo.resolve()
        if not repo.is_dir():
            raise ValueError(f"{repo} is not a directory")

        snippets_gen = get_snippets(
            root=repo,
            exclude_dir_if=exclude_dir_if,
            exclude_file_if=exclude_file_if,
        )

        self.table.add_snippets(snippets_gen)
        self.table.create_index(replace=True)
        return True

    def is_trained(self) -> bool:
        return self.table.has_index()

    def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 5,
        use_rerankers: Reranker | Iterable[Reranker] = (),
    ) -> pd.DataFrame:
        self.table.use_rerankers(use_rerankers)
        results = self.generator.search_snippets(query, language, limit)

        return results


if __name__ == "__main__":
    import sys
    from lancedb.rerankers import CrossEncoderReranker
    import warnings

    warnings.simplefilter('ignore')

    if len(sys.argv) < 2:
        print('Need at least 1 search query')
        exit()

    query: str = sys.argv[1]

    language: Optional[str] = None
    if len(sys.argv) == 3:
        language = sys.argv[2]

    engine = CodeSearchEngine('mkpro118', 'mkpro118-repository')

    print(f'Starting Training...')
    engine.train(
        exclude_dir_if=too_big,
        exclude_file_if=is_not_supported,
        pretrained_ok=True,
    )

    print(f'Training complete!')
    print(f'Query = {sys.argv[1]}')
    print(f'Using reranker = {CrossEncoderReranker}')

    results = engine.search(
        query=query, language=language, use_rerankers=CrossEncoderReranker()
    )
    print('Results')
    print(results)
    print(results[['filename', '_relevance_score']])
