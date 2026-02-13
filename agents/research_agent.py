import json
from dotenv import load_dotenv, find_dotenv

# Force load env to be safe, searching in parent directories
load_dotenv(find_dotenv(), override=True)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState
from core.llm import get_llm

class CompanyResearchAgent:
    def __init__(self):
        self.temperature = 0

    def research(self, state: AgentState) -> dict:
        """
        Analyzes company inputs and web content to produce a deep research report.
        """
        print(f"--- Researching Company: {state.get('company_name', 'Unknown')} ---")
        llm = get_llm(temperature=self.temperature)

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

        try:
            chain = prompt | llm | JsonOutputParser()
            result = chain.invoke({
                "web_content": web_content[:50000],
                "doc_content": doc_content[:50000]
            })
            return result
        except Exception as json_err:
            print(f"JSON parsing failed, trying string fallback: {json_err}")
            try:
                chain_str = prompt | llm | StrOutputParser()
                raw = chain_str.invoke({
                    "web_content": web_content[:50000],
                    "doc_content": doc_content[:50000]
                })
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    cleaned = "\n".join(lines)
                result = json.loads(cleaned)
                return result
            except Exception as fallback_err:
                print(f"String fallback also failed: {fallback_err}")
                errors = state.get("errors", [])
                errors.append({
                    "agent_name": "CompanyResearchAgent",
                    "error_type": "api_error",
                    "message": str(json_err),
                    "recoverable": True
                })
                return {
                    "company_name": state.get("company_name", "Unknown"),
                    "deep_research": f"Error during research: {str(json_err)}",
                    "errors": errors
                }

if __name__ == "__main__":
    # Test stub
    pass
