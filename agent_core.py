import pypdf
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from google import genai
from tavily import TavilyClient
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts text from an uploaded PDF file object"""
    reader = pypdf.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def analyze_resume(resume_text: str, api_key: str, model_provider: str = "openai") -> dict:
    """
    Analyzes the resume text to extract skills and suggest internship roles.
    Returns a dictionary with 'skills', 'suggested_roles', and 'summary'.
    """
    if model_provider == "openai":
        llm = ChatOpenAI(temperature=0.2, api_key=api_key, model="gpt-4o-mini")
        prompt = PromptTemplate.from_template(
            """You are an expert career advisor and technical recruiter. 
            Analyze the following student resume and extract key information to help them find an internship.
            
            Resume Text:
            {resume_text}
            
            Please provide the output STRICTLY in the following JSON format:
            {{
                "summary": "A 2-sentence summary of the student's profile.",
                "skills": ["skill1", "skill2", "..."],
                "suggested_roles": ["Role Title 1", "Role Title 2", "Role Title 3"]
            }}
            """
        )
        chain = prompt | llm
        response = chain.invoke({"resume_text": resume_text})
        content = response.content.strip()
        
    elif model_provider == "gemini":
        client = genai.Client(api_key=api_key)
        prompt_text = f"""You are an expert career advisor and technical recruiter. 
            Analyze the following student resume and extract key information to help them find an internship.
            
            Resume Text:
            {resume_text}
            
            Please provide the output STRICTLY in the following JSON format:
            {{
                "summary": "A 2-sentence summary of the student's profile.",
                "skills": ["skill1", "skill2", "..."],
                "suggested_roles": ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"]
            }}
            """
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt_text
        )
        content = response.text.strip()
    else:
        raise ValueError("Unsupported model provider")

    
    # Try to parse the JSON output
    try:
        # Strip markdown code blocks if the LLM adds them
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        return result
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {
            "summary": "Failed to analyze resume properly.",
            "skills": [],
            "suggested_roles": []
        }

def find_target_companies(roles: list, tavily_api_key: str, limit_per_role: int = 2) -> list:
    """
    Uses Tavily Search to find companies hiring for the suggested roles.
    Returns a list of dictionaries with company information.
    """
    tavily_client = TavilyClient(api_key=tavily_api_key)
    companies = []
    
    for role in roles:
        query = f"top tech companies hiring for '{role}' early career or internship positions"
        try:
            response = tavily_client.search(query=query, search_depth="advanced", max_results=5)
            # Just extract domain or titles as proxy for companies
            # In a real app we would use an LLM or NER model to extract exact company names from snippets
            
            # Simple extraction from titles for demonstration
            # We'll just collect the results as context, and let the generation phase use it 
            # or simply record the search titles/urls as "leads".
            
            for result in response.get("results", [])[:limit_per_role]:
                companies.append({
                    "role": role,
                    "lead_title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")
                })
        except Exception as e:
            print(f"Tavily search failed for role {role}: {e}")
            
    return companies

def generate_cold_emails(resume_summary: str, companies: list, api_key: str, model_provider: str = "openai") -> list:
    """
    Generates a personalized cold email for each company using the student's resume summary.
    """
    prompt_template = """You are an expert career advisor helping a student write a cold email for an internship.
        
        Student's Resume Summary:
        {resume_summary}
        
        Target Role: {role}
        Company Info / Lead Title: {lead_title}
        Company Context: {snippet}
        
        Write a short, professional, and confident cold email (max 4 sentences) to a recruiter at this company. 
        Don't use placeholders like [Your Name] if possible, just write the body. Mention the context or role.
        """

    if model_provider == "openai":
        llm = ChatOpenAI(temperature=0.4, api_key=api_key, model="gpt-4o-mini")
        prompt = PromptTemplate.from_template(prompt_template)
        chain = prompt | llm
        
        results = []
        for comp in companies:
            try:
                response = chain.invoke({
                    "resume_summary": resume_summary,
                    "role": comp['role'],
                    "lead_title": comp['lead_title'],
                    "snippet": comp['snippet']
                })
                comp['email_draft'] = response.content.strip()
            except Exception as e:
                comp['email_draft'] = f"Failed to generate draft: {e}"
            results.append(comp)
            
        return results

    elif model_provider == "gemini":
        client = genai.Client(api_key=api_key)
        
        results = []
        for comp in companies:
            try:
                formatted_prompt = prompt_template.format(
                    resume_summary=resume_summary,
                    role=comp['role'],
                    lead_title=comp['lead_title'],
                    snippet=comp['snippet']
                )
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=formatted_prompt
                )
                comp['email_draft'] = response.text.strip()
            except Exception as e:
                comp['email_draft'] = f"Failed to generate draft: {e}"
            results.append(comp)
            
        return results

    else:
        raise ValueError("Unsupported model provider")

def create_google_sheet(dataframe, credentials_path: str = "credentials.json", user_email: str = None) -> str:
    """
    Creates a new Google Sheet, populates it with the dataframe, and shares it with the user.
    Returns the URL of the created sheet.
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)
        
        # Create a new spreadsheet with a unique name
        sheet_name = f"Internship_Tracker_{str(uuid.uuid4())[:8]}"
        spreadsheet = client.create(sheet_name)
        
        # Share the sheet with the user if email provided, else make it readable for anyone with link
        if user_email:
            spreadsheet.share(user_email, perm_type='user', role='writer')
        else:
            spreadsheet.share(None, perm_type='anyone', role='reader')
            
        worksheet = spreadsheet.get_worksheet(0)
        
        # Format the data (convert everything to strings to avoid json serialization errors)
        formatted_df = dataframe.astype(str)
        # Prepare the data matrix [headers, row1, row2...]
        data_matrix = [formatted_df.columns.values.tolist()] + formatted_df.values.tolist()
        
        worksheet.update(data_matrix)
        
        return spreadsheet.url
        
    except FileNotFoundError:
        return "ERROR: credentials.json not found."
    except Exception as e:
        return f"ERROR: Failed to create Google Sheet: {e}"
