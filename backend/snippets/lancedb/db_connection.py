import dataclasses

from typing import Optional

import lancedb
from lancedb.db import DBConnection

from snippets.lancedb.table import SnippetTable


@dataclasses.dataclass
class SnippetDBConnection:  # type: ignore[misc]
    db: Optional[DBConnection] = None
    db_uri: Optional[str] = '.snippet-db'

    def __post_init__(self):
        # All good case
        if None not in (self.db, self.db_uri):
            return

        # All bad case, error
        if (None, None) == (self.db, self.db_uri):
            raise ValueError(
                f'Need at least one of db or db_uri not be {None}'
            )

        # Create connection from uri
        if self.db is None:
            self.db = lancedb.connect()
            return

        # Get uri from connection
        self.db_uri = self.db.uri()

    @classmethod
    def from_uri(cls, uri: str) -> 'SnippetDBConnection':
        db = lancedb.connect(uri=uri)
        return cls(db=db, db_uri=uri)

    @classmethod
    def from_db_connection(cls,  # type: ignore[misc]
                           db_connection: DBConnection) -> 'SnippetDBConnection':
        return cls(db=db_connection, db_uri=db_connection.uri())

    def get_or_create_table(self, table_name: str) -> SnippetTable:
        return SnippetTable()
