import dataclasses

from typing import Optional

import lancedb
from lancedb.db import DBConnection

from snippets.lancedb.config import DBConfig
from snippets.lancedb.factory import SnippetSchemaFactory
from snippets.lancedb.table import SnippetTable


@dataclasses.dataclass
class SnippetDBConnection:  # type: ignore[misc]
    config: DBConfig
    db: Optional[DBConnection] = None
    db_uri: Optional[str] = ".snippet-db"

    def __post_init__(self):
        # All bad case, error
        if (None, None) == (self.db, self.db_uri):
            raise ValueError(f"Need at least one of db or db_uri not be {None}")

        # Create connection from uri
        if self.db is None:
            self.db = lancedb.connect(self.db_uri)

        # Get uri from connection
        self.db_uri = self.db.uri

        # Initialize tables
        self.tables: dict[str, SnippetTable] = dict()

        self.use_config(self.config)

    def use_config(self, config: DBConfig) -> None:
        if not isinstance(config, DBConfig):
            raise TypeError(
                f"Table is not an instance of {type(DBConfig)}. "
                f"Found {type(config)}"
            )

        # _check_state() validates that self.configs is a list
        self.config = config
        self.schema = SnippetSchemaFactory.make_schema(self.config)

    def add_table(self, table: SnippetTable) -> None:
        if not isinstance(table, SnippetTable):
            raise TypeError(
                f"Table is not an instance of {type(SnippetTable)}. "
                f"Found {type(table)}"
            )

        self.tables.update({table.name: table})

    @classmethod
    def from_uri(cls, config: DBConfig, uri: str) -> "SnippetDBConnection":
        return cls(config=config, db_uri=uri)

    @classmethod
    def from_db_connection(  # type: ignore[misc]
        cls, config: DBConfig, db_connection: DBConnection
    ) -> "SnippetDBConnection":
        return cls(config=config, db=db_connection)

    def get_or_create_table(
        self, config: DBConfig, table_name: str
    ) -> SnippetTable:
        if table_name in self.tables:
            return self.tables[table_name]

        if self.db is None:
            raise ValueError("Invalid State, connection is invalid")

        table = self.db.create_table(
            name=table_name,
            schema=self.schema,
            exist_ok=True,  # Get or Create semantics
        )

        self.tables[table_name] = SnippetTable(
            config=config, name=table_name, table=table
        )

        return self.tables[table_name]
