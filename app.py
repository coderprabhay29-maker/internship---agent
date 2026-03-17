import streamlit as st
import os
import pandas as pd
import agent_core
from dotenv import load_dotenv

# Load Admin API keys
load_dotenv()

st.set_page_config(page_title="AI Internship Finder", page_icon="🎓", layout="wide")

# Custom CSS for polished UI
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
        color: white;
    }
    h1 {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🎓 AI Internship Finder</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload your resume. Let AI find you the perfect internship and draft your cold emails automatically.</p>', unsafe_allow_html=True)

# Fetch backend keys
llm_api_key = os.getenv("GEMINI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
llm_choice = "gemini" # Hardcoded optimal model

if not llm_api_key or not tavily_api_key:
    st.error("Admin Error: GEMINI_API_KEY or TAVILY_API_KEY is missing from the `.env` file. Please configure the backend.")
    st.stop()

# Settings Sidebar
with st.sidebar:
    st.header("📊 Google Sheets Auto-Export")
    st.markdown("*(Requires `credentials.json` in root folder)*")
    enable_sheets = st.checkbox("Export directly to Google Sheets?")
    google_email = st.text_input("Your Google Email (to share sheet with)")

# Main Interface
st.header("1. Upload Resume")
uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

if uploaded_file is not None:
    st.success("Resume uploaded successfully! (Processing coming in Phase 2)")
    
    st.header("2. AI Analysis & Recommendations")
    if st.button("Analyze Resume & Find Opportunities 🚀"):
        with st.spinner("AI is analyzing your resume..."):
            # Phase 2 implementation
            resume_text = agent_core.extract_text_from_pdf(uploaded_file)
            st.session_state['analysis_result'] = agent_core.analyze_resume(resume_text, llm_api_key, llm_choice)
            
            st.subheader("Resume Analysis")
            st.write(f"**Summary:** {st.session_state['analysis_result'].get('summary', '')}")
            st.write(f"**Top Skills:** {', '.join(st.session_state['analysis_result'].get('skills', []))}")
            st.write(f"**Suggested Roles:** {', '.join(st.session_state['analysis_result'].get('suggested_roles', []))}")
        
        with st.spinner("Searching for companies..."):
            # Phase 3 implementation
            roles = st.session_state['analysis_result'].get('suggested_roles', [])
            if roles:
                st.session_state['companies'] = agent_core.find_target_companies(roles, tavily_api_key)
                st.success(f"Found {len(st.session_state['companies'])} relevant company leads!")
            else:
                st.session_state['companies'] = []
        
        with st.spinner("Building your tracking sheet..."):
            # Phase 4 implementation
            if st.session_state['companies']:
                st.subheader("🎯 Tracking Sheet")
                df = pd.DataFrame(st.session_state['companies'])
                # Reorder and rename columns for readability
                if not df.empty:
                    df = df[['role', 'lead_title', 'url']]
                    df.columns = ['Target Role', 'Company/Lead', 'URL']
                    st.dataframe(df, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name='internship_tracker.csv',
                            mime='text/csv',
                        )
                        
                    with col2:
                        if enable_sheets:
                            if os.path.exists("credentials.json"):
                                with st.spinner("Generating Live Google Sheet..."):
                                    sheet_url = agent_core.create_google_sheet(df, "credentials.json", google_email)
                                    if "ERROR" in sheet_url:
                                        st.error(sheet_url)
                                    else:
                                        st.success("Google Sheet Created!")
                                        st.markdown(f"**[🔗 Click Here to Open Your Live Tracker]({sheet_url})**")
                            else:
                                st.error("`credentials.json` not found in the application directory. Cannot create live sheet.")
                else:
                    st.warning("No companies found to generate sheet.")
                
st.markdown("---")
st.caption("Built to streamline the internship search process for students. 🚀")
