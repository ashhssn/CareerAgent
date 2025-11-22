import os
from typing import TypedDict, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.tools import search_jobs, scrape_job_description

load_dotenv()

class AgentState(TypedDict):
    user_resume: str # from user
    job_search_query: str # from user
    found_job_urls: List[str] # from Researcher Node
    selected_job_details: str # from Selector Node
    final_cover_letter: str # from Writer node

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

def researcher_node(state: AgentState):
    print("--- NODE: RESEARCHER ---")
    query = state['job_search_query']
    urls = search_jobs(query)
    return {'found_job_urls': urls}

def scraper_node(state: AgentState):
    print("--- NODE: SCRAPER ---")
    urls = state['found_job_urls']
    if not urls:
        print("No urls found")
        return {'selected_job_details': 'No URLs found to scrape'}
    
    # we tale the first URL found for now
    target_url = urls[0]
    print(f"--- SCRAPING {target_url} ---")

    content = scrape_job_description(target_url)

    return {'selected_job_details': content}

def writer_node(state: AgentState):
    print("--- NODE: WRITER --- ")
    resume = state['user_resume']
    job_details = state['selected_job_details']

    prompt_template = """
    You are a professional career coach.
    
    Target Job Description:
    {job_details}
    
    Candidate Resume:
    {resume}
    
    Task:
    Write a professional cover letter tailored to this job description using the candidate's resume. 
    Focus on why the candidate is a great fit.
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    response = chain.invoke({'job_details': job_details, 'resume': resume})

    return {'final_cover_letter': response.content}

def build_graph():
    """
    Constructs the StateGraph workflow
    """
    workflow = StateGraph(AgentState)

    # adding nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("scraper", scraper_node)
    workflow.add_node("writer", writer_node)

    # add edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "scraper")
    workflow.add_edge("scraper", "writer")
    workflow.add_edge("writer", END)

    return workflow.compile()

