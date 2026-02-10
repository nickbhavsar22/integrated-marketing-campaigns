import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.state import AgentState

class JTBDAnalyst:
    def __init__(self):
        # Using Gemini 1.5 Pro
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0.2,
            google_api_key=api_key,
            max_retries=10
        )

    def analyze_jobs(self, state: AgentState) -> dict:
        """
        Maps Jobs to be Done (JTBD) for each persona.
        """
        brief = state.get("campaign_brief", {})
        personas = state.get("personas", [])
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a JTBD (Jobs to be Done) Expert.
            For the defined campaign and personas, list the specific "jobs" they are trying to hire a solution for.
            
            **Campaign Context:**
            {brief}
            
            **Personas:**
            {personas}
            
            1. Analyze the Personas and Campaign Brief to identify high-value Jobs to be Done.
            2. Generate a list of 4-6 distinct JTBDs across the identified personas.
            3. **STRATEGIC ASSET MIX:** For EACH job, you MUST explicitly assign a `recommended_asset_type`.
               - **Mandatory Diversity:** You MUST include at least 3 different asset types in the final list.
               - **Options:** Blog Post, LinkedIn Post, Email Sequence, Whitepaper, Case Study, Webinar Script, Landing Page.
               - **Selection Logic:** 
                 - Awareness Stage -> LinkedIn Post, Blog Post.
                 - Evaluation Stage -> Whitepaper, Case Study, Webinar Script.
                 - Decision Stage -> Landing Page, Email Sequence (Nurture).
            
            **Output Format:**
            JSON List of objects. KEY "recommended_asset_type" IS MANDATORY.
            [
                {{
                    "persona_role": "Title",
                    "jtbd": "Specific job...",
                    "burning_question": "What specifically are they asking?",
                    "recommended_asset_type": "Asset Type",
                    "buying_stage": "Awareness|Evaluation|Decision"
                }}
            ]
            """
        )
        
        chain = prompt | self.llm | JsonOutputParser()
        try:
            result = chain.invoke({"brief": str(brief), "personas": str(personas)})
            # Ensure result is a list
            if isinstance(result, dict) and "jobs" in result:
                result = result["jobs"]
            return {"content_manifest": result}
        except Exception as e:
            print(f"Error in JTBD: {e}")
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "JTBDAnalyst",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {"content_manifest": [], "errors": errors}
