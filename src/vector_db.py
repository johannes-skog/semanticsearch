from typing import Dict, Any, List
import weaviate

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
        
        if self.exists is False:
            self._setup_class(schema)
            
    def _setup_class(self, schema):
        
        assert schema["class"] == self._name
        
        self._client.schema.create_class(schema)
        
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
            "properties": properties
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