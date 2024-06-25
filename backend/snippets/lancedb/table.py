import dataclasses

from collections.abc import Iterable, Iterator

from lancedb.table import Table

from snippets import Snippet
from snippets.lancedb.config import DBConfig
from snippets.lancedb.db_connection import SnippetDBConnection
from snippets.lancedb.factory import SnippetSchemaFactory


@dataclasses.dataclass
class SnippetTable:
    config: DBConfig
    name: str
    db: SnippetDBConnection
    factory: SnippetSchemaFactory
    exist_ok: bool = False

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
