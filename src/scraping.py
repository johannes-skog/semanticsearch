import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import uuid
import multiprocessing as mp

def generate_uuid(identifier: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, identifier))

class SwedishLegislationScraper:
    
    MAPPING = {
        "5_result-inner-box": "issuer",
        "7_result-inner-box": "issued_date",
        "9_result-inner-box": "in_effect_date",
        "11_result-inner-box": "content",
        "1_result-inner-box bold": "SFS_number",
        "3_result-inner-box": "title",
    }
    
    @staticmethod
    def extract_content_single(post_id):

        url = f"https://rkrattsbaser.gov.se/sfsr?fritext=&upph=false&sort=desc&page=2&post_id={post_id}"

        # Send a request to the URL
        response = requests.get(url)

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the "Visa fulltext" link
        fulltext_element = soup.find("a", href=True, text=lambda text: "Visa fulltext" in text if text else False)

        fulltext_link = fulltext_element["href"]
    
        fulltext_url = f"https://rkrattsbaser.gov.se{fulltext_link}"

        # Send a request to the fulltext URL
        fulltext_response = requests.get(fulltext_url)

        # Parse the HTML content of the fulltext page
        fulltext_soup = BeautifulSoup(fulltext_response.text, "html.parser")

        # Find the elements in the HTML structure
        main_wrapper = fulltext_soup.find(class_="main wrapper")
        content = main_wrapper.find(class_="content")
        search_results = content.find(class_="search-results")
        search_main = search_results.find(class_="search-main")
        search_results_content = search_main.find(class_="search-results-content")

        # Initialize the output dictionary
        output = {}

        # Iterate through the children of 'search-results-content', adding them to the dictionary with index and class name
        for index, child in enumerate(search_results_content.children):
            if child.name is not None:
                class_name = " ".join(child["class"])
                key = f"{index}_{class_name}"
                output[key] = child.get_text(strip=True)
                
        output = {
            SwedishLegislationScraper.MAPPING[k] :v for k, v in output.items() if k in SwedishLegislationScraper.MAPPING.keys()
        }

        return output

def post_process_swedish_legislation(df: pd.DataFrame):
    """Post-process the scraped data. This function is specific to the Swedish legislation scraper."""
    
    df.SFS_number = df.SFS_number.transform(lambda x: x.split()[2])
    df.issued_date = df.issued_date.str.replace("Utfärdad:", "")
    return df 

def scan_swedish_legislation_parallel(n_posts=4541):
    """Scan the Swedish legislation database for all posts."""

    with mp.Pool() as pool:

        jobs = [pool.apply_async(
            SwedishLegislationScraper.extract_content_single, args=(post_id,)) for post_id in range(1, n_posts - 1)
        ]

        # Collect the results
        outputs = [job.get() for job in tqdm(jobs)]

    df = pd.DataFrame(outputs)
    df = post_process_swedish_legislation(df)

    return df
