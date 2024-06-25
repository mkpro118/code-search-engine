import os
import pathlib

from typing import Any, Callable, Generator, Iterable, Optional

from lancedb.rerankers import Reranker

from snippets import Snippet
from snippets.languages import Language
from snippets.lancedb.config import ST_Config
from snippets.lancedb.db_connection import SnippetDBConnection
from snippets.lancedb.generator import SnippetGenerator


def get_snippets(
    root: str | pathlib.Path,
    exclude_dir_if: Callable[[str], bool],
    exclude_file_if: Callable[[str], bool],
    # ) -> Generator[Snippet, None, None]:
) -> list[Snippet]:
    l = list()
    for root, dirs, files in os.walk(str(root)):
        dirs[:] = [d for d in dirs if not exclude_dir_if(d)]

        for file in files:
            if exclude_file_if(file):
                continue

            fp = pathlib.Path(root) / file
            l.append(Snippet.from_file(fp).to_dict())
    return l


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
    def __init__(self, table_name: str):
        self.config = ST_Config()
        self.db = SnippetDBConnection.from_uri(self.config, "mkpro118_db")
        self.db.db.drop_table(table_name)
        self.table = self.db.get_or_create_table(self.config, table_name)
        self.generator = SnippetGenerator(table=self.table)

    def train(
        self,
        repo: str | pathlib.Path,
        use_rerankers: Reranker | Iterable[Reranker] = (),
    ) -> None:
        if not isinstance(repo, pathlib.Path):
            repo = pathlib.Path(repo)

        repo = repo.resolve()
        if not repo.is_dir():
            raise ValueError(f"{repo} is not a directory")

        snippets_gen = get_snippets(
            root=repo,
            exclude_dir_if=too_big,
            exclude_file_if=is_not_supported,
        )

        self.table.add_snippets(snippets_gen)
        self.table.use_rerankers(use_rerankers)

    def search(
        self, query: str, language: Optional[str] = None, limit: int = 5
    ) -> Any:
        results = self.generator.search_snippets(query, language, limit)

        return results


if __name__ == "__main__":
    engine = CodeSearchEngine("mkpro118-snippets")

    from lancedb.rerankers import CrossEncoderReranker

    engine.train(
        "./gh_data/repos/mkpro118/mkpro118-repository/",
        use_rerankers=CrossEncoderReranker(),
    )
