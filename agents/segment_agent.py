from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.state import AgentState
from core.llm import get_llm

class MarketSegmentAgent:
    def __init__(self):
        self.temperature = 0.2

    def analyze(self, state: AgentState) -> dict:
        """
        Identifies market segments and buying committee personas based on deep research.
        """
        research = state.get("deep_research", "")
        llm = get_llm(temperature=self.temperature)

        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert Go-To-Market Strategist.
            Based on the provided company research, identify the core Market Segments and the Buying Committee Personas.

            **Research Context:**
            {research}

            **Task:**
            1. **Segments:** Identify 2-3 ideal market segments (Industries/Verticals) this company should target.
            2. **Personas:** For the TOP segment, identify the Buying Committee members (e.g., Economic Buyer, Champion, User, Technical Evaluator).

            **Output Format:**
            Return a JSON object with two keys: "segments" (list) and "personas" (list).

            Example JSON Structure:
            {{
                "segments": [
                    {{"name": "Enterprise Fintech", "rationale": "..."}},
                    ...
                ],
                "personas": [
                    {{"role": "CTO", "type": "Economic Buyer", "job_to_be_done": "Reduce infrastructure costs", "pain_points": ["High maintenance", "Security risks"]}},
                    ...
                ]
            }}
            """
        )

        chain = prompt | llm | JsonOutputParser()

        try:
            result = chain.invoke({"research": research})
            return {
                "segments": result.get("segments", []),
                "personas": result.get("personas", [])
            }
        except Exception as e:
            print(f"Error in MarketSegmentAgent: {e}")
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "MarketSegmentAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {"segments": [], "personas": [], "errors": errors}

if __name__ == "__main__":
    pass
