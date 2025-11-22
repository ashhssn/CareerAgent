import os
from typing import List
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import WebBaseLoader
from pypdf import PdfReader

load_dotenv()

def search_jobs(query: str) -> List[dict]:
    """
    Searches the web for job listings using Tavily.
    Returns a list of dictionaries
    """

    tool = TavilySearch(
        max_results=5,
        country='Singapore'
    )

    try:
        ret = tool.invoke({'query': query})

        return ret['results']
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
    
def read_resume_from_pdf(file_path: str) -> str:
    """
    Extracts content from a resume in PDF.
    Returns the content.
    """
    reader = PdfReader(file_path)
    content = ""
    for page in reader.pages:
        content += page.extract_text() + "\n"
    return content