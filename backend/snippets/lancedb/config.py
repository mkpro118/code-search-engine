import dataclasses

from lancedb.embeddings import get_registry
from lancedb.embeddings.base import EmbeddingFunction, TextEmbeddingFunction
from lancedb.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddings as ST_Embeddings
)


@dataclasses.dataclass
class DBConfig:  # type: ignore[misc]
    registery: EmbeddingFunction
    model: TextEmbeddingFunction


# ST is SentenceTransformer
class ST_Config(DBConfig):
    registery: ST_Embeddings = get_registry().get('sentence-transformers')
    model: ST_Embeddings = registery.create(name='BAAI/bge-small-en-v1.5')
