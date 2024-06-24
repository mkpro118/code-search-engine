import dataclasses

from lancedb.table import Table

from snippets.lancedb.config import ST_Config
from snippets.lancedb.db_connection import SnippetDBConnection
from snippets.lancedb.factory import SnippetSchemaFactory


@dataclasses.dataclass
class SnippetTable:
    config: ST_Config
    name: str
    db: SnippetDBConnection
    exist_ok: bool = False

    def __post_init__(self):
        self.table: Table
        db = self.db.db

        if db is None:
            raise ValueError(
                f'SnippetDBConnection object {self.db} does not '
                'define a lancedb.db.DBConnection. Invalid SnippetDBConnection'
            )

        try:
            self.table = db.create_table(
                name=self.name,
                schema=SnippetSchemaFactory.get_schema(config=self.config),
                exist_ok=self.exist_ok
            )
        except OSError:
            self.table = db.open_table(self.name)

    # def add_snippets(self, snippet: Snippet):
    #     pass
