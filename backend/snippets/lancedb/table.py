import dataclasses

import pandas as pd

from collections.abc import Iterable, Iterator
from typing import cast, Literal, Optional

from lancedb.table import Table
from lancedb.rerankers import Reranker

import pyarrow.fs as pa_fs

from snippets import Snippet
from snippets.lancedb.config import DBConfig


@dataclasses.dataclass
class SnippetTable:  # type: ignore[misc]
    config: DBConfig
    name: str
    table: Table
    rerankers: list[Reranker] = dataclasses.field(default_factory=list)

    def add_snippets(
        self, snippets: Snippet | Iterable[Snippet] | Iterator[Snippet]
    ) -> None:

        if isinstance(snippets, Snippet):
            snippets = [snippets]

        dicts = map(Snippet.to_dict, snippets)

        self.table.add(pd.DataFrame(dicts))

    def create_index(self, replace: bool = False) -> None:
        self.table.create_fts_index("text", replace=replace)

    def has_index(self) -> bool:
        fs, path = pa_fs.FileSystem.from_uri(self.table._get_fts_index_path())

        # Mypy could not infer type
        # See https://stackoverflow.com/a/75865051
        return cast(
            bool, fs.get_file_info(path).type != pa_fs.FileType.NotFound
        )

    def use_rerankers(self, reranker: Reranker | Iterable[Reranker]) -> None:
        if isinstance(reranker, Reranker):
            self.rerankers.append(reranker)
        elif isinstance(reranker, Iterable):
            self.rerankers.extend(reranker)
        else:
            raise TypeError(f"Invalid type {type(reranker)}")

    def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int | Literal[5] = 5,
        use_rerankers: bool = True,
    ) -> pd.DataFrame:
        srch = self.table.search(query, query_type="hybrid")

        if language:
            srch = srch.where(f'language = "{language}"', prefilter=True)

        if use_rerankers:
            for reranker in self.rerankers:
                srch = srch.rerank(reranker=reranker)

        srch = srch.limit(limit=limit)

        # Mypy could not infer type
        return cast(pd.DataFrame, srch.to_pandas())
