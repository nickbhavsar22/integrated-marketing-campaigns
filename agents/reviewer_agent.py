from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState
from core.llm import get_llm

class ReviewerAgent:
    def __init__(self):
        self.temperature = 0

    def review_campaign(self, state: AgentState) -> dict:
        """
        Reviews the entire campaign output against PRD goals.
        """
        print("--- Reviewing Campaign Alignment with PRD ---")
        llm = get_llm(temperature=self.temperature)

        company_name = state.get("company_name", "the Client")
        strategy = state.get("strategy_framework", "")
        brief = state.get("campaign_brief", {})
        assets = state.get("generated_assets", [])

        # Format assets for prompt
        assets_summary = "\n".join([f"- {a.get('type')}: {a.get('title')}" for a in assets])

        prompt = ChatPromptTemplate.from_template(
            """
            You are a Senior Strategic Reviewer and PRD Auditor.
            Your goal is to evaluate if the generated marketing materials for {company_name} align with the project goals.

            **PRD Goals Context:**
            - Build an AI-powered system that orchestrates multi-persona, multi-stage marketing campaigns.
            - Address specific "Jobs to be Done" (JTBD) for each purchasing decision-maker.
            - Provide deeply personalized, segment-specific content.

            **Current Output to Review:**

            **Strategy Framework:**
            {strategy}

            **Campaign Brief:**
            {brief}

            **Generated Assets:**
            {assets_summary}

            **Evaluation Criteria:**
            1. **Multi-Persona Coverage:** Does the campaign address multiple buying committee members?
            2. **Multi-Stage Funnel:** Are assets provided for different stages (Awareness, Evaluation, Decision)?
            3. **JTBD Alignment:** Is the content clearly solving the specific jobs-to-be-done identified?
            4. **Strategic Consistency:** Does the messaging in the assets match the Strategy Framework?

            **Output Format (JSON):**
            Provide your audit in a structured JSON object with the following keys:
            - "score": A numeric compliance score (0-100).
            - "markdown_report": A concise audit report in Markdown including "Strengths" and "Gaps".
            - "refinement_instructions": If the score is below 90, provide specific, actionable instructions for the Content Agent on how to fix the gaps. If above 90, this can be "Perfect as is".
            """
        )

        from langchain_core.output_parsers import JsonOutputParser
        chain = prompt | llm | JsonOutputParser()

        try:
            result = chain.invoke({
                "company_name": company_name,
                "strategy": strategy,
                "brief": str(brief),
                "assets_summary": assets_summary
            })

            return {
                "reviewer_feedback": result.get("markdown_report", ""),
                "reviewer_score": result.get("score", 0),
                "refinement_instructions": result.get("refinement_instructions", "")
            }
        except Exception as e:
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "ReviewerAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {
                "reviewer_feedback": f"Review Error: {str(e)}",
                "reviewer_score": 0,
                "refinement_instructions": "Please retry generation.",
                "errors": errors
            }

if __name__ == "__main__":
    pass
