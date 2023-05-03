from typing import Dict, Any, List
import weaviate
from embedd import Embedder
from tqdm import tqdm
import numpy as np

class VectorDatabase(object):
    
    def __init__(self, name: str):
        
        self._name = name
        
    def _exists(self):
        pass
    
class VectorDatabaseWeaviate(VectorDatabase):

    def __init__(
        self,
        name,
        url: str,
        schema: Dict[str, Any]
    ):
        
        super().__init__(
            name=name,
        )
        
        assert name[0].isupper(), "First letter is not capitalized, Weaviate will complain..."
        
        self._client = weaviate.Client(
          url=url
        )

        self._schema = schema
        
        if self.exists is False:
            self._setup_class(self._schema)
            
    def _setup_class(self, schema):
        
        assert schema["class"] == self._name
        
        self._client.schema.create_class(schema)
    
    def redo(self):

        try: 
            self.delete()
        except Exception as e:
            print(e)
    
        self._setup_class(self._schema)

    @property
    def data(self):

        return self._client.data_object.get(self._name)

    def delete(self):

        try: 
            self._client.schema.delete_class(self._name)
        except Exception as e:
            print(e)

    @property
    def data_entries(self):
        return [x["name"] for x in self._schema["properties"]]

    def search(
        self,
        search_vector: List[float],
        limit: int = 10,
        return_data_entries: List[str] = None,
        return_distance: bool = True,
        return_vector: bool = False,
    ):

        return_data_entries = (
            return_data_entries if return_data_entries is not None else self.data_entries
        )

        additional = ["id"]

        if return_distance:
            additional.append("distance")
        if return_vector:
            additional.append("vector")

        results = self._client.query.get(
            self._name, return_data_entries
        ).with_near_vector(
            {"vector": search_vector}
        ).with_additional(
            additional
        ).with_limit(limit).do()

        return results

    @staticmethod
    def setup_class_object_structure(
        class_name: str,
        names: List[str],
        data_types: List[str],
        description: str,
    ):

        properties = [
            {
                "name": name,
                "dataType": [dataType],
            }
            for name, dataType in zip(names, data_types)
        ]

        class_obj = {
            "class": class_name,
            "vectorizer": "none", # we are providing the vectors so this field is none
            "description": description,
            "properties": properties,
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "space": "cosine",
                "m": 128,
                "efConstruction": 16,
                "ef": 250,
                "maxConnections": 32
            }
        }

        return class_obj
        
    @property
    def exists(self):
    
        current_schema = self._client.schema.get()
        
        exists = False
        
        for class_obj in current_schema['classes']:
           
            class_name = class_obj['class']
            
            if self._name == class_name:
                exists = True
                break
            
        return exists
    
    def populate(self, embedder: Embedder, batch_size: int = 10):

        i = 0

        with self._client.batch as batch:  # Context manager manages batch flushing
            batch.batch_size = batch_size
            batch.dynamic=True
            for data_obj in tqdm(embedder):

                i +=1

                vector = data_obj[Embedder.EMBEDDING_COLUMN]

                if vector is None:
                    continue

                del data_obj[Embedder.EMBEDDING_COLUMN]

                try:
                    batch.add_data_object(data_obj, self._name, vector=vector)
                except Exception as e:
                    print(e)