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
    found_job_urls: List[dict] # from Researcher Node
    selected_job_url: str # from Selector Node
    selected_job_details: str # from Scraper Node
    final_cover_letter: str # from Writer node

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

def researcher_node(state: AgentState):
    print("--- NODE: RESEARCHER ---")
    query = state['job_search_query']
    results = search_jobs(query)
    return {'found_job_urls': results}

def selector_node(state: AgentState):
    print("--- NODE: SELECTOR ---")
    results = state['found_job_urls']

    options_text = ""
    for i, res in enumerate(results):
        options_text += f"{i+1}. URL: {res['url']}\n Snippet: {res['content']}\n\n"

    prompt_template = """
    You are a Job Hunt Expert. Your task is to identify the single best URL to scrape for a job description.
    
    USER QUERY: {query}
    
    SEARCH RESULTS:
    {options_text}
    
    INSTRUCTIONS:
    - Select the URL that looks like a DIRECT job listing (not a blog, not a listicle, not a general career page).
    - If multiple look good, pick the one that matches the query best.
    - Return ONLY the URL. Nothing else. No markdown.
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm

    response = chain.invoke({
        'query': state['job_search_query'],
        'options_text': options_text
    })

    chosen_url = response.content.strip()
    print(f"AI has selected: {chosen_url}")

    return {'selected_job_url': chosen_url}

def scraper_node(state: AgentState):
    print("--- NODE: SCRAPER ---")
    target_url = state['selected_job_url']
    
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
    workflow.add_node("selector", selector_node)
    workflow.add_node("scraper", scraper_node)
    workflow.add_node("writer", writer_node)

    # add edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "selector")
    workflow.add_edge("selector", "scraper")
    workflow.add_edge("scraper", "writer")
    workflow.add_edge("writer", END)

    return workflow.compile()

