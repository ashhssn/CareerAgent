import streamlit as st
from src.graph import build_graph
import sys
from contextlib import contextmanager
from io import StringIO

@contextmanager
def st_capture(output_func):
    """A context manager to capture stdout and display it in a Streamlit container."""
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write

        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret

        stdout.write = new_write
        yield

@contextmanager
def redirect_stdout(new_target):
    """Temporarily redirect stdout."""
    old_target, sys.stdout = sys.stdout, new_target
    try:
        yield new_target
    finally:
        sys.stdout = old_target

st.set_page_config(page_title="CareerAgent", page_icon="🕵️‍♂️")

st.title("🕵️‍♂️ CareerAgent: AI Job Hunter")
st.markdown("Pairs your resume with live job listings to draft custom cover letters.")

# sidebar
with st.sidebar:
    st.header("Your Details")
    user_resume = st.text_area(
        "Paste your Resume/CV here:",
        height=300,
        value="John Doe. Python Developer with 3 years experience in AI..."
    )
    
    st.header("Job Preferences")
    job_query = st.text_input(
        "What job are you looking for?",
        value="Python AI Agent Developer Remote"
    )
    
    submit_btn = st.button("Start Headhunting")

# main area
if submit_btn:
    if not user_resume or not job_query:
        st.error("Please provide both a resume and a job query.")
    else:
        status_container = st.empty()
        
        try:
            # run the agent
            app = build_graph()
            inputs = {
                "user_resume": user_resume,
                "job_search_query": job_query
            }
            
            with st.spinner("Agent is working... (Researching -> Selecting -> Scraping -> Writing)", show_time=True):
                with st.expander("Agent Steps"):
                    log_container = st.empty()

                    with st_capture(log_container.code):
                        result = app.invoke(inputs)
                
            # get the results to display
            final_letter = result.get('final_cover_letter')
            search_results = result.get('found_job_results', [])
            selected_url = result.get('selected_job_url')
    
            st.success("Job Done!")
            
            st.subheader("Generated Cover Letter")
            st.markdown(final_letter)
            
            # transparency section
            with st.expander("View Search Logic (Debug)"):
                st.info(f"**AI Selected this URL:** {selected_url}")
                
                st.write("---")
                st.write("**All Search Results:**")
                for res in search_results:
                    # Handle cases where Tavily might return partial data
                    url = res.get('url', 'No URL')
                    snippet = res.get('content', 'No snippet')[:100] # Preview
                    st.markdown(f"- **[{url}]({url})**: _{snippet}..._")
                        
        except Exception as e:
            st.error(f"An error occurred: {e}")