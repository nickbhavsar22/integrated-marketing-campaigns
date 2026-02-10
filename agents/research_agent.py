import os
from dotenv import load_dotenv, find_dotenv

# Force load env to be safe, searching in parent directories
load_dotenv(find_dotenv(), override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState

class CompanyResearchAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        print(f"API key: {'configured' if api_key else 'MISSING'}")

        # Using Gemini 1.5 Pro for its large context window as requested
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0,
            google_api_key=api_key,
            max_retries=10
        )

    def research(self, state: AgentState) -> dict:
        """
        Analyzes company inputs and web content to produce a deep research report.
        """
        print(f"--- Researching Company: {state.get('company_name', 'Unknown')} ---")
        
        web_content = state.get("raw_web_content", "")
        doc_content = state.get("raw_doc_content", "")
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a minimalist but deep-thinking Senior Market Analyst.
            
            Your goal is to perform a DEEP RESEARCH analysis on the company described below and identify the Company Name.
            
            **Input Data:**
            - Web Content: {web_content}
            - Internal Documents: {doc_content}
            
            **Task:**
            1. **Extract Company Name:** Identify the official or commonly used name of the company from the provided data.
            2. **Deep Research Report:**
               - **Core Identity:** What does this company actually do? What is their "One Thing"?
               - **Value Proposition:** What is the specific value they promise? "So What?" (Why does it matter?)
               - **Market Position:** Where do they sit in the market ecosystem? (Leader, Challenger, Niche player?)
               - **Brand Voice:** Analyze the tone of the inputs (e.g., specific, authoritative, playful, corporate).
            
            **Output Format (JSON):**
            {{
                "company_name": "The Extracted Name",
                "deep_research": "The full Markdown report content here..."
            }}
            """
        )
        
        from langchain_core.output_parsers import JsonOutputParser
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = chain.invoke({
                "web_content": web_content[:50000],
                "doc_content": doc_content[:50000]
            })
            return result
        except Exception as e:
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "CompanyResearchAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {
                "company_name": "Unknown",
                "deep_research": f"Error during research: {str(e)}",
                "errors": errors
            }

if __name__ == "__main__":
    # Test stub
    pass
