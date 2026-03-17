# 🎓 AI Internship Finder Agent

An AI-powered agent built with Python and Streamlit that automates the internship search and cold outreach process for students!

## Features
- **Resume Parsing**: Upload a student resume (PDF), and Gemini extracts top skills and matches them to 3 ideal internship roles.
- **Company Discovery Engine**: Integrates with the Tavily AI Search API to dynamically scrape the live web for tech companies actively hiring for those specific roles.
- **AI Cold Email Generator**: Uses Gemini 2.5 Flash to automatically draft highly personalized, 4-sentence cold emails for every single company returned, referencing the student's background and the company description.
- **Live Output Tracking**: Instantly generates a clean Pandas DataFrame tracking sheet containing the Roles, Companies, URLs, and Cold Emails.
- **Seamless Exports**: Download the tracker directly as a `.csv` file, or automatically push it to a live Google Sheet using a Service Account.

## Setup Instructions

### 1. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/[your-username]/internship-finder-agent.git
cd internship-finder-agent
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Keys
You will need two API keys to run the agent. Create a `.env` file in the root directory and add the following:

```env
GEMINI_API_KEY="your_google_gemini_api_key"
TAVILY_API_KEY="your_tavily_api_key"
```

1. **Google Gemini API Key** (Free): Get it from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Tavily Search API Key** (Free Tier): Get it from [Tavily](https://app.tavily.com)

*(Optional) Google Sheets Integration:*
If you want the agent to auto-generate live Google Sheets, you must place a Google Cloud Service Account `credentials.json` file in the root directory and ensure the Google Drive and Google Sheets APIs are enabled on your Google Cloud project.

### 3. Running the App
Start the Streamlit web interface:
```bash
streamlit run app.py
```
Open the provided Localhost URL and upload a resume to start searching! No manual API key entry is required by the end-user.

## Tech Stack
- **Frontend**: Streamlit
- **LLM Engine**: Google Gemini (via `google-genai` native SDK)
- **Web Search**: Tavily API
- **Data Export**: Pandas & `gspread` (Google Sheets API)
