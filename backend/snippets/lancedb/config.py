import dataclasses

from lancedb.embeddings import get_registry
from lancedb.embeddings.base import EmbeddingFunction, TextEmbeddingFunction
from lancedb.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddings as ST_Embeddings
)

_defaults = {'registry': get_registry().get('sentence-transformers')}

_defaults.update({
    'model': _defaults['registry'].create(name='BAAI/bge-small-en-v1.5')
})


@dataclasses.dataclass(frozen=True)
class DBConfig:  # type: ignore[misc]
    registry: EmbeddingFunction
    model: TextEmbeddingFunction


# ST is SentenceTransformer
class ST_Config(DBConfig):
    registry: ST_Embeddings = dataclasses.field(default=_defaults['registry'])
    model: ST_Embeddings = dataclasses.field(default=_defaults['model'])
