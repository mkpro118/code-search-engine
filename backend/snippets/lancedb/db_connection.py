import dataclasses

from typing import Optional

import lancedb
from lancedb.db import DBConnection

from snippets.lancedb.config import DBConfig
from snippets.lancedb.factory import SnippetSchemaFactory
from snippets.lancedb.table import SnippetTable


@dataclasses.dataclass
class SnippetDBConnection:  # type: ignore[misc]
    configs: DBConfig | list[DBConfig]
    db: Optional[DBConnection] = None
    db_uri: Optional[str] = ".snippet-db"

    def __post_init__(self):
        # All good case
        if None not in (self.db, self.db_uri):
            return

        # All bad case, error
        if (None, None) == (self.db, self.db_uri):
            raise ValueError(f"Need at least one of db or db_uri not be {None}")

        if isinstance(self.configs, DBConfig):
            self.configs = [self.configs]
        else:
            self.configs = list(self.configs)

        # Create connection from uri
        if self.db is None:
            self.db = lancedb.connect()
            return

        # Get uri from connection
        self.db_uri = self.db.uri()

        # Initialize tables
        self.tables: dict[str, SnippetTable] = dict()

        # Initialize factory
        self.factory = SnippetSchemaFactory()

        for config in self.configs:
            self.factory.register(config)

    def _check_state(self) -> None:
        if not isinstance(self.configs, list):
            raise ValueError(
                "Invalid state, expected self.configs to be a list"
            )

    def add_config(self, config: DBConfig) -> None:
        if not isinstance(config, DBConfig):
            raise TypeError(
                f"Table is not an instance of {type(DBConfig)}. "
                f"Found {type(config)}"
            )

        self._check_state()

        # _check_state() validates that self.configs is a list
        self.configs.append(config)  # type: ignore[union-attr]
        self.factory.register(config)

    def add_table(self, table: SnippetTable) -> None:
        self._check_state()

        # _check_state() validates that self.configs is a list
        for config in self.configs:  # type: ignore[union-attr]
            if table.config == self.configs:
                break
        else:
            raise ValueError(
                "No registered configurations found that match",
                "the table configuration",
            )
        if not isinstance(table, SnippetTable):
            raise TypeError(
                f"Table is not an instance of {type(SnippetTable)}. "
                f"Found {type(table)}"
            )

        self.tables.update({table.name: table})

    @classmethod
    def from_uri(cls, config: DBConfig, uri: str) -> "SnippetDBConnection":
        return cls(configs=config, db_uri=uri)

    @classmethod
    def from_db_connection(  # type: ignore[misc]
        cls, config: DBConfig, db_connection: DBConnection
    ) -> "SnippetDBConnection":
        return cls(configs=config, db=db_connection)

    def get_or_create_table(
        self, config: DBConfig, table_name: str
    ) -> SnippetTable:
        if table_name in self.tables:
            return self.tables[table_name]

        self._check_state()

        self.tables[table_name] = SnippetTable(
            config=config, name=table_name, db=self, factory=self.factory
        )

        return self.tables[table_name]
