import os
from typing import List
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import WebBaseLoader

load_dotenv()

def search_jobs(query: str) -> List[str]:
    """
    Searches the web for job listings using Tavily.
    Returns a list of URLs
    """

    tool = TavilySearch(
        max_results=3
    )

    try:
        ret = tool.invoke({'query': query})
        results = ret['results']

        urls = [res['url'] for res in results if 'url' in res]
        return urls
    except Exception as e:
        print(f"Error in search_jobs: {e}")
        return []
    
def scrape_job_description(url: str) -> str:
    """
    Scrapes text content from a specific url
    """
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()

        # combine content from all loaded docs
        full_text = "\n\n".join([d.page_content for d in docs])

        return full_text.strip()
    except Exception as e:
        return f"Error in scraping {url}: {e}"