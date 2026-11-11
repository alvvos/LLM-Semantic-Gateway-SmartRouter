import numpy as np
import os
import redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.query import Query
from redis.commands.search.index_definition import IndexDefinition, IndexType
from sentence_transformers import SentenceTransformer
import hashlib

class RedisSemanticCache:
    def __init__(self, host='localhost', port=6379, model_name='all-MiniLM-L6-v2', threshold=0.82, dimension=384):
        print(f"Conectando a Redis en {host}:{port} y cargando {model_name}.")
        
        self.redis = redis.Redis(host=host, port=port, decode_responses=False)
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.dimension = dimension
        self.index_name = "idx:semantic_cache"
        
        self._setup_index()

    def _setup_index(self):
        """Crea el índice vectorial en Redis si no existe."""
        try:
            self.redis.ft(self.index_name).info()
        except redis.exceptions.ResponseError:
            schema = (
                TextField("response"),
                VectorField(
                    "embedding", 
                    "FLAT", 
                    {
                        "TYPE": "FLOAT32", 
                        "DIM": self.dimension, 
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )

            # "namespace isolation"
            definition = IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
            self.redis.ft(self.index_name).create_index(fields=schema, definition=definition)

    def search(self, query: str):
        query_vector = self.model.encode([query])[0].astype(np.float32).tobytes()
        
        q = (
            Query("*=>[KNN 1 @embedding $vec AS distance]")
            .return_fields("response", "distance")
            .sort_by("distance")
            .dialect(2)
        )
        
        res = self.redis.ft(self.index_name).search(q, query_params={"vec": query_vector})
        
        if res.docs:
            distance = float(res.docs[0].distance)

            # Invertimos la escala para darle un sentido más natural
            similarity = 1.0 - distance
            
            if similarity >= self.threshold:
                return res.docs[0].response, similarity
            else:
                # Si estamos por debajo del umbral de confianza, devolvemos el None como mensaje, pero el índice de similitud real
                return None, similarity
                
        return None, 0.0

    def add(self, query: str, response: str):
        """Guarda la pregunta (hash), la respuesta y el vector en Redis."""
        vector = self.model.encode([query])[0].astype(np.float32).tobytes()
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()

        # Esta técnica se conoce como "namespaces isolation".
        doc_id = f"cache:{query_hash}"
        
        # El ACK del server responde con la cantidad de campos insertados, se lanza cuando el insert llega a la RAM, no a disco de manera segura.
        self.redis.hset(doc_id, mapping={
            "response": response,
            "embedding": vector
        })


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

cache_instance = RedisSemanticCache(host=redis_host, port=redis_port)