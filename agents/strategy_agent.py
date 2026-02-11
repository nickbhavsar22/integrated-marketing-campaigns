import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState

class StrategyAgent:
    def __init__(self):
        # Using Gemini 1.5 Pro
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0.3,
            google_api_key=api_key,
            max_retries=2
        )

    def develop_strategy(self, state: AgentState) -> dict:
        """
        Drafts key positioning and messaging frameworks.
        """
        research = state.get("deep_research", "")
        segments = state.get("segments", [])
        competitors = state.get("competitor_analysis", "")
        company_name = state.get("company_name", "the Client")
        brand_voice = state.get("brand_voice", "")
        brand_tone = state.get("brand_tone", "")
        messaging_pillars = state.get("messaging_pillars", [])

        # Convert segments list to string for prompt
        segments_str = str(segments)

        brand_guidelines_block = ""
        if brand_voice or brand_tone or messaging_pillars:
            pillars_str = ", ".join(messaging_pillars) if messaging_pillars else "N/A"
            brand_guidelines_block = f"""
            **BRAND GUIDELINES (Must be reflected in all messaging):**
            - Voice: {brand_voice or 'Not specified'}
            - Tone: {brand_tone or 'Not specified'}
            - Key Pillars: {pillars_str}
            """

        prompt = ChatPromptTemplate.from_template(
            """
            You are a Chief Marketing Officer (CMO) for {company_name}.
            Develop a high-level Positioning and Messaging Framework strategy.

            **Context:**
            - Company: {company_name}
            - Research: {research}
            - Competitors: {competitors}
            - Target Segments: {segments_str}
            {brand_guidelines_block}

            **Requirements:**
            1. **Core Positioning Statement:** (For [Internal], who [Statement of Need], {company_name} is a [Category] that [Statement of Benefit]...)
            2. **Key Messaging Pillars:** 3 core themes {company_name} must hit to win against competitors.
            3. **Differentiation:** Explicitly state how {company_name} sounds different from the competitors found in the analysis.

            Output as Markdown.
            """
        )

        chain = prompt | self.llm | StrOutputParser()
        try:
            result = chain.invoke({
                "company_name": company_name,
                "research": research,
                "competitors": competitors,
                "segments_str": segments_str,
                "brand_guidelines_block": brand_guidelines_block
            })
            return {"strategy_framework": result}
        except Exception as e:
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "StrategyAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {"strategy_framework": f"Error in StrategyAgent: {str(e)}", "errors": errors}
