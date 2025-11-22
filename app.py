import streamlit as st
from src.graph import build_graph
from src.tools import read_resume_from_pdf
import os

st.set_page_config(page_title="CareerAgent", page_icon="🕵️‍♂️", layout="wide")

st.title("CareerAgent: AI Career Architect")
st.markdown("Analyzes your fit for a specific job AND finds new opportunities simultaneously.")

# sidebar
with st.sidebar:
    st.header("Your Details")
    user_resume = st.file_uploader(
        "Upload your Resume (in .pdf)",
        type="pdf"
    )
    
    st.header("Target Job Analysis")
    target_url = st.text_input(
        "Paste a specific Job URL to analyze:"
    )
    
    submit_btn = st.button("Start Analysis")

# main area
if submit_btn:
    if not user_resume or not target_url:
        st.error("Please provide both a PDF resume and a Target Job URL.")
    else:
        try:
            # temporarily save pdf
            with open("temp_resume.pdf", "wb") as f:
                f.write(user_resume.getbuffer())
            
            # extract resume text
            resume_text = read_resume_from_pdf("temp_resume.pdf")

            # remove temp pdf
            os.remove("temp_resume.pdf")
            
            # build graph
            app = build_graph()
            inputs = {
                "resume_text": resume_text,
                "target_url": target_url
            }
            
            # Run agentic workflow
            with st.status("Agent is working...", expanded=False) as status:
                # TODO: find a way to stream intermediate steps to UI without blocking ThreadPoolExecutor
                st.write("1. Profiling Resume...")
                st.write("2. Searching for Jobs (Track A)...")
                st.write("3. Analyzing Target URL (Track B)...")
                
                result = app.invoke(inputs)
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)
            
            # get results to display
            gap_analysis = result.get('gap_analysis')
            found_jobs = result.get('found_job_urls', [])
            search_query = result.get('generated_search_query')
            
            col1, col2 = st.columns([0.6, 0.4])
            
            with col1:
                st.subheader("📝 Deep Dive Analysis")
                st.markdown(gap_analysis)
                
            with col2:
                st.subheader("Similar Opportunities")
                st.info(f"**AI Search Query:** `{search_query}`")
                
                if found_jobs:
                    for job in found_jobs:
                        url = job.get('url')
                        content = job.get('content', '')[:150]
                        st.markdown(f"**🔗 [Open Job Link]({url})**")
                        st.caption(f"{content}...")
                        st.divider()
                else:
                    st.warning("No additional similar jobs found.")
                        
        except Exception as e:
            st.error(f"An error occurred: {e}")
            # print to streamlit for debugging
            st.write(e)