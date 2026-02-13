import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState
from core.llm import get_llm

class CompetitorAgent:
    def __init__(self):
        self.temperature = 0.1

    def _fetch_tavily_intel(self, company_name: str) -> str:
        """Fetch real-time competitor intelligence via Tavily search."""
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            print("--- Tavily API key not set, using LLM-only competitor analysis ---")
            return ""
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=tavily_key)
            results = tavily.search(
                query=f"{company_name} competitors alternatives",
                search_depth="advanced",
                max_results=5
            )
            summaries = []
            for r in results.get("results", []):
                summaries.append(f"- **{r.get('title', 'N/A')}**: {r.get('content', '')[:300]}")
            if summaries:
                return "\n\n**REAL-TIME COMPETITIVE INTELLIGENCE (Tavily):**\n" + "\n".join(summaries)
            return ""
        except Exception as e:
            print(f"--- Tavily search failed, falling back to LLM-only: {e} ---")
            return ""

    def analyze(self, state: AgentState) -> dict:
        """
        Performs competitive analysis based on the research.
        """
        research = state.get("deep_research", "")
        company_name = state.get("company_name", "")
        llm = get_llm(temperature=self.temperature)

        tavily_intel = self._fetch_tavily_intel(company_name)

        prompt = ChatPromptTemplate.from_template(
            """
            You are a Competitive Intelligence Analyst.
            Based on the deep research provided, conduct a competitive landscape analysis.

            **Research Context:**
            {research}
            {tavily_intel}

            **Task:**
            1. Identify 3-5 likely competitors based on the company's value_prop.
            2. Analyze the "Positioning Gap" - where does this company win where others fail?
            3. Create a "Battlecard" summary for the top competitor.

            Produce a Markdown report.
            """
        )

        chain = prompt | llm | StrOutputParser()

        try:
            result = chain.invoke({"research": research, "tavily_intel": tavily_intel})
            return {"competitor_analysis": result}
        except Exception as e:
            errors = state.get("errors", [])
            errors.append({
                "agent_name": "CompetitorAgent",
                "error_type": "api_error",
                "message": str(e),
                "recoverable": True
            })
            return {
                "competitor_analysis": f"Error in CompetitorAgent: {str(e)}",
                "errors": errors
            }

if __name__ == "__main__":
    pass
