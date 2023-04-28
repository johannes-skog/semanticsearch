
import pandas as pd 
from typing import List
import tiktoken
import openai

def split_text(text: str, chunk_size: int, overlap: int):
    """Split a text into chunks of a given size, with a given overlap between chunks."""
    chunks = []
    start = 0
    end = chunk_size
    while start < len(text):
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        end += chunk_size - overlap
    return chunks

class Embedder(object):
    
    EMBEDDING_COLUMN = "vector"
    
    def __init__(
        self,
        df: pd.DataFrame,
        embedd_column: str,
        text_max_length: int,
        text_overlap: int,
        context_columns: List[str] = None,
    ):
        
        self._text_max_length = text_max_length
        self._text_overlap = text_overlap
        
        self._df = df
        self._embedd_column = embedd_column
        self._context_columns = context_columns
        
    def setup(self):
        
        self._split_process()
        self._add_context()
        
        self._df = self._df.reset_index(drop=True)
        
    def _split_process(self):
        
        self._df[self._embedd_column] = (
            self._df[self._embedd_column].apply(
                lambda x: split_text(str(x), self._text_max_length , self._text_overlap)
            )
        )
        
        self._df = self._df.explode(self._embedd_column)
        
    def _add_context(self):
    
        for context_column in self._context_columns:
            self._df[self._embedd_column] = (
                self._df[context_column] + "||" + 
                self._df[self._embedd_column]
            )
            
    def _get_iter_item(self, index):
        
        d = self._df.loc[index]
        
        return d.to_dict()
            
    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._df):
            raise StopIteration
        else:
            item = self._get_iter_item(self._index)
            self._index += 1
            return item
        
class EmbedderOpenAI(Embedder):

    def __init__(
        self,
        df: pd.DataFrame,
        embedd_column: str,
        text_max_length: int,
        text_overlap: int,
        model_name: str,
        context_columns: List[str] = None,
    ):
        
        super().__init__(
            df=df,
            embedd_column="content",
            text_max_length=text_max_length,
            text_overlap=text_overlap,
            context_columns=context_columns,
        )
        
        self._model_name = model_name
        
        self._tokenizer = tiktoken.encoding_for_model(self._model_name)
        
    def setup(self):
        
        self._split_process()
        
        self._add_context()
        
        self._number_tokens()
        
        self._df = self._df.reset_index(drop=True)
        
    def _prepare_for_embedding(self, text):
        
        text = str(text)
        
        text = text.replace("\n", " ").replace("\r", " ")
        
        return text
    
    def _number_tokens(self):
        
        self._df["n_tokens"] = self._df[self._embedd_column].apply(
            lambda x: len(self._tokenizer.encode(self._prepare_for_embedding(x)))
        )
    
    def embedd_single(self, text):
        
        text = self._prepare_for_embedding(text)
        
        return openai.Embedding.create(input=[text], model=self._model_name)['data'][0]['embedding']
    
    def embedd(self, limit_tokens = 2000):
        
        assert all(self._df["n_tokens"] < limit_tokens)
        
        self._df[self.EMBEDDING_COLUMN] = self._df[self._embedd_column].transform(
            lambda x: self.embedd_single(x)
        )
    
