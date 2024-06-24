from lancedb.pydantic import LanceModel, Vector

from snippets.lancedb.config import DBConfig, ST_Config


class SnippetSchemaFactory:
    @staticmethod
    def get_schema(config: DBConfig) -> LanceModel:  # type: ignore[misc]
        if isinstance(config, ST_Config):
            return SnippetSchemaFactory._sentence_transformer(config)

    @staticmethod
    def _sentence_transformer(config: ST_Config) -> LanceModel:  # type: ignore[misc]
        class SnippetSchema(LanceModel):  # type: ignore[misc]
            text: str = config.model.SourceField()
            vector: Vector(384) = config.model.VectorField()  # type: ignore[valid-type]
            language: str
