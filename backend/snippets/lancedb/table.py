import dataclasses

import pandas as pd

from collections.abc import Iterable, Iterator
from typing import cast, Literal, Optional

from lancedb.table import Table
from lancedb.rerankers import Reranker

from snippets import Snippet
from snippets.lancedb.config import DBConfig
from snippets.lancedb.db_connection import SnippetDBConnection
from snippets.lancedb.factory import SnippetSchemaFactory


@dataclasses.dataclass
class SnippetTable:  # type: ignore[misc]
    config: DBConfig
    name: str
    db: SnippetDBConnection
    factory: SnippetSchemaFactory
    exist_ok: bool = False
    rerankers: list[Reranker] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        self.table: Table
        db = self.db.db

        if db is None:
            raise ValueError(
                f"SnippetDBConnection object {self.db} does not "
                "define a lancedb.db.DBConnection. Invalid SnippetDBConnection"
            )

        try:
            self.table = db.create_table(
                name=self.name,
                schema=self.factory.get_schema(config=self.config),
                exist_ok=self.exist_ok,
            )
        except OSError:
            self.table = db.open_table(self.name)

    def add_snippets(
        self, snippets: Snippet | Iterable[Snippet] | Iterator[Snippet]
    ) -> None:

        if isinstance(snippets, Snippet):
            snippets = [snippets]

        dicts = map(Snippet.to_dict, snippets)
        self.table.add(dicts)

    def use_reranker(self, reranker: Reranker | Iterable[Reranker]) -> None:
        self.rerankers.append(reranker)

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

        return cast(pd.DataFrame, srch.to_pandas())
