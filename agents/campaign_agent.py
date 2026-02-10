import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.state import AgentState

class CampaignArchitectAgent:
    def __init__(self):
        # Using Gemini 1.5 Pro
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0.4,
            google_api_key=api_key,
            max_retries=10
        )

    def create_brief(self, state: AgentState) -> dict:
        """
        Creates a structured campaign brief.
        """
        strategy = state.get("strategy_framework", "")
        personas = state.get("personas", [])
        segments = state.get("segments", [])
        company_name = state.get("company_name", "the Client")
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a Campaign Manager for {company_name}.
            Create a Campaign Brief based on the strategy.
            
            **Strategy:**
            {strategy}
            
            **Available Segments:**
            {segments}
            
            **Personas:**
            {personas}
            
            **Task:**
            1. Analyze the research and segments to select **EXACTLY ONE** Primary Target Segment.
            2. High-value selection: Choose the segment with the highest growth potential OR the clearest pain point alignment.
            3. Build the campaign strategy around this specific segment.
            
            **Output:**
            Create a JSON object representing the Brief. You MUST include 'primary_target_segment' and 'segment_rationale'.
            {{
                "company_name": "{company_name}",
                "campaign_name": "Strategic Campaign Name",
                "primary_target_segment": "Name of the ONE selected segment",
                "segment_rationale": "Detailed strategic justification for why THIS segment was chosen over others.",
                "primary_target_persona": "The lead persona within this segment",
                "objective": "Clear, measurable business goal (e.g., Increase demo requests by 20%)",
                "core_theme": "The overarching creative/strategic angle",
                "target_audience_summary": "Who we are talking to and why they care",
                "key_messages": ["Message 1", "Message 2", "Message 3"],
                "funnel_stage_focus": "Awareness|Evaluation|Decision"
            }}
            """
        )
        
        chain = prompt | self.llm | JsonOutputParser()
        try:
            result = chain.invoke({
                "company_name": company_name,
                "strategy": strategy,
                "personas": str(personas),
                "segments": str(segments)
            })
            return {"campaign_brief": result}
        except Exception as e:
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "CampaignArchitectAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {"campaign_brief": {"error": str(e)}, "errors": errors}
