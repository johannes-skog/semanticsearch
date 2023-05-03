from typing import Callable
import os
import openai
from vector_db import VectorDatabaseWeaviate
from embedd import EmbedderSwedishLegislation
import logging 

class SwedishLegislationSearch(object):
    
    def __init__(
        self,
        embedd_function: Callable,
        vector_db: VectorDatabaseWeaviate,
    ):
        
        self._embedd_function = embedd_function
        self._vector_db = vector_db
        
    def search(self, text, limit: int = 5):
        
        v = self._embedd_function(
            text
        )
        
        results = self._vector_db.search(
            search_vector=v,
            limit=limit,
            return_data_entries=["content"],
            return_distance=False,
            return_vector=False,
        )
        
        texts = "\n".join([x["content"] for x in results["data"]["Get"][self._vector_db._name]])
        
        return texts
    
    def _wrap_query(self, query: str):

        s = "Svara på frågan med hjälp av de lagar och förordningar som du har tillgång till, referera alltid till källan."

        text = f"{s}\n{query}"
        
        return text
        
    def query(self, query: str, limit: int, return_context: bool = False, print_debug: bool = False):
        
        context = self.search(query, limit)
        
        query = self._wrap_query(
            query=query,
        )

        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
              {"role": "system", "content": "Du är en expert på Svensk lag, du svarar alltid tydligt med referenser till dina källor i texten som du har fått. Referera aldrig till några externa websidor."},
              {"role": "user", "content": context},
              {"role": "user", "content": query}
          ],
          temperature=0,
          top_p=1,
          frequency_penalty=0.0,
          presence_penalty=0.0,
        )
        
        response = response["choices"][0]["message"]["content"]

        return_data = {
            "response": response,
            "context": context if return_context else None,
        }

        if print_debug:
            print("###########CONTEXT###########\n\n" + context + "\n" * 2)
            print("###########QUERY###########\n\n" + query + "\n" * 2)
            print("###########RESPONSE###########\n\n" + response)

        return return_data
