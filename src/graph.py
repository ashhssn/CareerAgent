import os
from typing import TypedDict, List
from dotenv import load_dotenv
import json

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.tools import search_jobs, scrape_job_description
from helpers.prompts import RESUME_PROMPT, GAP_ANALYSIS_PROMPT

load_dotenv()

class AgentState(TypedDict):
    resume_text: str # user input
    target_url: str # user input
    profile_summary: str # llm will generate
    generated_search_query: str # llm will generate
    found_job_urls: List[str] # researcher node
    gap_analysis: str # analysis by llm
    job_description_text: str

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

def profiler_node(state: AgentState):
    print("--- NODE: PROFILER ---")
    resume = state['resume_text']

    prompt = ChatPromptTemplate.from_template(RESUME_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        'resume_text': resume
    })
    content = response.content.strip()

    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
    try:
        data = json.loads(content)
    except Exception as e:
        print(f"Error parsing json: {e}")
        return
    
    return {'profile_summary': data['overview'], 'generated_search_query': data['search_query']}

def researcher_node(state: AgentState):
    print("--- NODE: RESEARCHER ---")
    query = state['generated_search_query']
    results = search_jobs(query)
    return {'found_job_urls': results}

def scraper_node(state: AgentState):
    print("--- NODE: SCRAPER ---")
    target_url = state['target_url']
    
    print(f"--- SCRAPING {target_url} ---")
    content = scrape_job_description(target_url)

    return {'job_description_text': content[:15000]}

def analyzer_node(state: AgentState):
    print("--- NODE: ANALYZER ---")
    resume = state['resume_text']
    job_desc = state['job_description_text']

    prompt = ChatPromptTemplate.from_template(GAP_ANALYSIS_PROMPT)
    chain = prompt | llm
    response = chain.invoke({
        'resume': resume,
        'job_description': job_desc
    })

    return {'gap_analysis': response.content}


def build_graph():
    """
    Constructs the StateGraph workflow
    """
    workflow = StateGraph(AgentState)

    # adding nodes
    workflow.add_node("profiler", profiler_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("scraper", scraper_node)

    # add edges
    workflow.set_entry_point("profiler")
    workflow.add_edge("profiler", "researcher")
    workflow.add_edge("profiler", "scraper")
    workflow.add_edge("scraper", "analyzer")
    workflow.add_edge("researcher", END)
    workflow.add_edge("analyzer", END)
    
    return workflow.compile()

