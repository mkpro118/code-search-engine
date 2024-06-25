import dataclasses

from lancedb.pydantic import LanceModel, Vector

from snippets.lancedb.config import DBConfig


class SnippetSchemaFactory:
    @staticmethod
    def make_schema(config: DBConfig) -> LanceModel:  # type: ignore[misc]
        class _Schema(LanceModel):  # type: ignore[misc]
            text: str = config.model.SourceField()
            vector: Vector(384) = config.model.VectorField()  # type: ignore[valid-type]
            language: str
            filename: str

        return _Schema
