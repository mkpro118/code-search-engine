import dataclasses

from lancedb.pydantic import LanceModel, Vector

from snippets.lancedb.config import DBConfig


@dataclasses.dataclass
class SnippetSchemaFactory:  # type: ignore[misc]
    registry: dict[DBConfig, type[LanceModel]] = dataclasses.field(default_factory=dict)

    def register(self, config: DBConfig) -> None:
        if not isinstance(config, DBConfig):
            raise TypeError(
                'Registration must be done with a DBConfig '
                '(or a subclass) instance'
            )

        schema = SnippetSchemaFactory.make_schema(config)

        self.registry[config] = schema

    def get_schema(self, config: DBConfig) -> LanceModel:
        if not isinstance(config, DBConfig):
            raise TypeError(
                f'Cannot get schema for type {type(config)} ',
                'Registered schemas are DBConfig instances'
            )

        if config not in self.registry:
            raise ValueError(f'No registered schemas for {config}')

        return self.registry[config]

    @staticmethod
    def make_schema(config: DBConfig) -> LanceModel:  # type: ignore[misc]
        class _Schema(LanceModel):  # type: ignore[misc]
            text: str = config.model.SourceField()
            vector: Vector(384) = config.model.VectorField()  # type: ignore[valid-type]
            language: str

        return _Schema
