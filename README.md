# Semantic Search With Chat Interface

This repository contains a semantic search implementation with a chat interface, utilizing OpenAI's embedding models and chat completion models.

The code implements semantic search with a chat interface for Swedish legislation and regulations. It can easily be extended to handle other cases as well. The code includes a custom scraping tool for riksdagen.se to extract all current legislation and regulations.

* Context is embedded and stored in a vector database (Weaviate)
* During the search, the query is embedded and compared against the embedded contexts stored in the vector database. The nearest matches are extracted and used as context for a chat completion call to answer the initial query.

## Getting Started

To get started on you will need to build development container and the Weaviate service container:

```sh
make build
```

To start the containers:

```sh
make up
```

and then to enter the development container:

```sh
make enter
```

## Swedish Legislations and Regulations segmantic Search with Chat Interface 

### 1. Scrape Swedish legislation data 
First, you need to scrape the Swedish government's website for all laws and regulations:

```python
from scraping import scan_swedish_legislation_parallel
df = scan_swedish_legislation_parallel()
```

### 2. Set up embedding

Next, set up the embedding process using the EmbedderSwedishLegislation class. This class is responsible for embedding the scraped legislation text:

```python
from embedd import EmbedderSwedishLegislation
embedder = EmbedderSwedishLegislation(
    df=df,
    embedd_column="content",
    text_max_length=1500,
    text_overlap=150,
    context_columns=["title"],
)
embedder.setup()
```

Some legislation and regulations are too lengthy to be embedded, by using `text_max_length` the text will be split into chunks containing at most `text_max_length` characters, `text_overlap` will ensure that we have an overlap between the different text chunks. 

### 3. Run the embedder

Now, run the embedder to process the legislation text:

```python
embedder.embedd(1000, timeout=1.01)
```

depening on your rate-limit for OpenAI api calls you might want to adjust the timeout. 


### 4. Set up vector database

Set up the Weaviate vector database using the VectorDatabaseWeaviate class:

```python
from vector_db import VectorDatabaseWeaviate

class_obj = VectorDatabaseWeaviate.setup_class_object_structure(
    class_name="Swedish_legislation",
    names=[
        "SFS_number", "title", "issuer", "content"
    ],
    data_types=["text"] * 4,
    description="Holds Swedish legislation"
)

vector_db = VectorDatabaseWeaviate(
    name="Swedish_legislation",
    url="http://weaviate:8080",
    schema=class_obj,
)
```

`class_obj` specifies the schema for the database class. 

### 5. Populate the vector database

Add the embedding vectors to the vector database:

```python
vector_db.populate(
    embedder=embedder,
    batch_size=10,
)
```

### 6. Set up the semantic search

Now, set up the semantic search with the SwedishLegislationSearch class:


```python
from search import SwedishLegislationSearch
law_search = SwedishLegislationSearch(
    embedd_function=EmbedderSwedishLegislation.embedd_single,
    vector_db=vector_db,
)
```

### 7. Perform a search query

Finally, you can perform a search query using natural language:

```python
return_data = law_search.query("Vilket ansvar har polisen under ett krigstillstånd? Svara detaljerat", limit=25, print_debug=True)
```

```
###########CONTEXT###########

....
....
....

Lag (1943:881) om polisens ställning under krig||varsmakten. Lag (2014:581). 3 § Har upphävts genom lag (2014:581). 4 § Har upphävts genom lag (1980:587). 5 § Regeringen meddelar närmare föreskrifter om tillämpningen av denna lag. Lag (2014:581).
Lag (1979:1088) om gränsövervakningen i krig m.m.||ten ska bedrivas, 2. vilka polismän, särskilt förordnade passkontrollanter och tulltjänstemän som ska avdelas för verksamheten och vilka militära enheter som ska medverka i denna, 3. hur personalen ska utbildas och utrustas, 4. vilken mate
Lag (1979:1088) om gränsövervakningen i krig m.m.||atta åtgärder. Om Försvarsmakten, Polismyndigheten eller Tullverket ska besluta om fortsatta åtgärder ska ärendet i stället överlämnas dit. Lag (2014:684). 8 § Om en skärpning av kontrollen av persontrafiken till eller från utlandet med visst 
Förordning (1982:756) om Försvarsmaktens ingripanden vid kränkningar av Sveriges territorium under fred och neutralitet, m.m. (IKFN-förordning)||smyndigheten. Om Polismyndigheten begär det, ska personalen hållas kvar i avvaktan på vidare åtgärder. Om det är nödvändigt får Försvarsmakten tillgripa vapenmakt. Det som nu har sagts gäller inte ambulansluftfartyg. Förordning (2014:1213). 54

....
....
....


###########QUERY###########

Svara på frågan med hjälp av de lagar och förordningar som du har tillgång till, referera alltid till källan.
Vilket ansvar har polisen under ett krigstillstånd? Svara detaljerat


###########RESPONSE###########

Enligt Lag (1943:881) om polisens ställning under krig är en polisman skyldig att delta i rikets försvar i den omfattning regeringen föreskriver. En polisman som enligt särskilda bestämmelser ska delta i rikets försvar tillhör under krig Försvarsmakten. Polismyndigheten kan begära medverkan av Polismyndigheten om polisiär medverkan är nödvändig för att avvärja ett fientligt angrepp. 

Enligt Kungörelse (1958:262) om tillämpning av lagen (1943:881) om polisens ställning under krig kan polismän avdelas för att fullgöra nödvändiga civila försvarsuppgifter eller medverkan allvarligt skulle äventyra den allmänna ordningen och säkerheten. När den begärda uppgiften har slutförts får Försvarsmakten inte förfoga över polismännen. 

Polismyndigheten har även ansvar för gränsövervakningen i krig enligt Lag (1979:1088) om gränsövervakningen i krig m.m. Polismyndigheten, Tullverket, Försvarsmakten och Kustbevakningen ska samordna övervakningen av trafiken över rikets gränser. 

Vidare kan polisen använda skjutvapen om gruppen, avdelningen eller någon annan utsätts för ett så allvarligt angrepp eller hot om angrepp att vapen måste användas omedelbart enligt Kungörelse (1969:84) om polisens användning av skjutvapen. 

Referenser:
- Lag (1943:881) om polisens ställning under krig
- Kungörelse (1958:262) om tillämpning av lagen (1943:881) om polisens ställning under krig
- Lag (1979:1088) om gränsövervakningen i krig m.m.
- Kungörelse (1969:84) om polisens användning av skjutvapen
```

