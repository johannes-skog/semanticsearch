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
law_search.query("När blir det inte tillåtet att köpa en ny bensinbil? Svara detaljerat", limit=5, print_debug=True)
```

```
###########CONTEXT###########

....(2011:846) om miljökrav vid upphandling av bilar och vissa tjänster inom vägtransportområdet avses ett motorfordon försett med ett drivsystem som innehåller minst en icke-perifer elektrisk maskin som energiomvandlare med ett elektriskt uppladdningsbart energilagringssystem som kan laddas externt. 3 § Med alternativa drivmedel i lagen (2011:846) om miljökrav vid upphandling av bilar och vissa tjänster inom vägtransportområdet avses bland annat - el, - väte, - biodrivmedel enligt definitionen i lagen (2010:598) om hållbarhetskriterier för biodrivmedel och biobränslen, - syntetiska och paraffiniska bränslen, - metangas, och - gasol. Med alternativa drivmedel avses däremot inte - biodrivmedel som är producerade från råvaror med hög ....


###########QUERY###########

Svara på frågan med hjälp av de lagar och förordningar som du har tillgång till, referera alltid till källan.
När blir det inte tillåtet att köpa en ny bensinbil? Svara detaljerat


###########RESPONSE###########

Det finns ingen specifik lag eller förordning som förbjuder köp av nya bensinbilar. Dock har Sverige och EU satt upp mål för att minska utsläppen av växthusgaser och främja en övergång till mer hållbara transportalternativ. 

Enligt Förordning (2022:315) om miljökrav vid upphandling av bilar och vissa tjänster inom vägtransportområdet, definieras elfordon och alternativa drivmedel som el, väte, biodrivmedel, syntetiska och paraffiniska bränslen, metangas och gasol. Däremot specificeras det att biodrivmedel som är producerade från råvaror med hög risk för indirekt ändring av markanvändning inte räknas som alternativa drivmedel. 

För att främja en övergång till mer hållbara transportalternativ har Sverige satt upp mål om att ha en fossiloberoende fordonsflotta senast år 2030. Enligt Förordning (2022:206) om statligt stöd till försäljningsställen för drivmedel i vissa landsbygdsområden, kan statligt stöd ges till försäljningsställen för drivmedel i vissa landsbygdsområden för att främja tillgången till alternativa drivmedel. 

Det finns också en ny Förordning (2023:132) om producentansvar för bilar som reglerar producenternas ansvar för att ta emot uttjänta bilar och se till att minst 95 procent av bilens vikt återanvänds eller återvinns. 

Sammanfattningsvis finns det ingen specifik lag eller förordning som förbjuder köp av nya bensinbilar, men det finns mål och regleringar som främjar en övergång till mer hållbara transportalternativ och minskade utsläpp av växthusgaser. 

Källor:
- Förordning (2022:206) om statligt stöd till försäljningsställen för drivmedel i vissa landsbygdsområden
- Förordning (2022:315) om miljökrav vid upphandling av bilar och vissa tjänster inom vägtransportområdet
- Förordning (2023:132) om producentansvar för bilar
```

