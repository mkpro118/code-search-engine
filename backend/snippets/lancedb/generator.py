import dataclasses
from typing import Optional
import pandas as pd

from snippets.lancedb.table import SnippetTable


@dataclasses.dataclass
class SnippetGenerator:
    table: SnippetTable

    def generate_response(
        self, query: str, language: Optional[str] = None, limit: int = 5
    ) -> list[str]:
        # Search for relevant snippets
        search_results = self.search_snippets(query, language, limit)

        # Generate a response based on the search results
        response = self._format_response(query, search_results)

        return response

    def search_snippets(
        self, query: str, language: Optional[str] = None, limit: int = 5
    ) -> pd.DataFrame:
        return self.table.search(query=query, language=language, limit=limit)

    def _format_response(self, query: str, search_results: pd.DataFrame) -> str:
        response = f"Query: {query}\n\nRelevant snippets:\n\n"

        for _, row in search_results.iterrows():
            response += f"Language: {row['language']}\n"
            response += f"Snippet:\n{row['text']}\n\n"
            response += "-" * 40 + "\n\n"

        return response
