from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.research_agent import CompanyResearchAgent
from agents.segment_agent import MarketSegmentAgent
from agents.competitor_agent import CompetitorAgent
from agents.strategy_agent import StrategyAgent
from agents.campaign_agent import CampaignArchitectAgent
from agents.jtbd_agent import JTBDAnalyst
from utils.scraper import WebScraper
from utils.doc_loader import DocumentLoader

# Initialize Agents
research_agent = CompanyResearchAgent()
segment_agent = MarketSegmentAgent()
competitor_agent = CompetitorAgent()
strategy_agent = StrategyAgent()
campaign_agent = CampaignArchitectAgent()
jtbd_agent = JTBDAnalyst()
scraper = WebScraper()

# Node Functions
def input_node(state: AgentState):
    """
    Scrapes the URL and loads documents.
    """
    print("--- Input Node ---")
    url = state.get("company_url")
    files = state.get("uploaded_files", [])
    files_dir = "data"
    
    web_content = ""
    if url:
        web_content = scraper.scrape(url)
    
    # Load docs (simplified loading of all valid files in data dir for now)
    # Ideally we filter by the specific files uploaded in this session if passed
    loader = DocumentLoader(files_dir)
    doc_content = "\n".join(loader.load_files())
    
    return {
        "raw_web_content": web_content,
        "raw_doc_content": doc_content
    }

def research_node(state: AgentState):
    return research_agent.research(state)

def segment_node(state: AgentState):
    return segment_agent.analyze(state)

def competitor_node(state: AgentState):
    return competitor_agent.analyze(state)

def strategy_node(state: AgentState):
    return strategy_agent.develop_strategy(state)

def campaign_node(state: AgentState):
    return campaign_agent.create_brief(state)

def jtbd_node(state: AgentState):
    return jtbd_agent.analyze_jobs(state)

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("inputs", input_node)
workflow.add_node("research", research_node)
workflow.add_node("segmentation", segment_node)
workflow.add_node("competitors", competitor_node)
workflow.add_node("strategy", strategy_node)
workflow.add_node("campaign_briefing", campaign_node)
workflow.add_node("jtbd_analysis", jtbd_node)

workflow.set_entry_point("inputs")
workflow.add_edge("inputs", "research")
workflow.add_edge("research", "segmentation")
workflow.add_edge("segmentation", "competitors")
workflow.add_edge("competitors", "strategy")
workflow.add_edge("strategy", "campaign_briefing")
workflow.add_edge("campaign_briefing", "jtbd_analysis")
workflow.add_edge("jtbd_analysis", END)

# Compile Main Graph
app_graph = workflow.compile()

# --- Generation Graph ---
from agents.content_agent import ContentCreatorAgent
from agents.promo_agent import PromotionalAgent
from agents.reviewer_agent import ReviewerAgent

content_agent = ContentCreatorAgent()
promo_agent = PromotionalAgent()
reviewer_agent = ReviewerAgent()

def content_node(state: AgentState):
    return content_agent.batch_generate(state)

def promo_node(state: AgentState):
    return promo_agent.batch_promote(state)

def review_node(state: AgentState):
    return reviewer_agent.review_campaign(state)

def increment_refinement(state: AgentState):
    count = state.get("refinement_count", 0)
    return {"refinement_count": count + 1}

def should_refine(state: AgentState):
    score = state.get("reviewer_score", 0)
    count = state.get("refinement_count", 0)
    threshold = state.get("refinement_threshold", 80)
    max_refs = state.get("max_refinements", 2)
    if score < threshold and count < max_refs:
        print(f"--- Refinement Triggered (Score: {score}/{threshold}, Loop: {count+1}/{max_refs}) ---")
        return "refine"
    return "end"

gen_workflow = StateGraph(AgentState)
gen_workflow.add_node("content_creation", content_node)
gen_workflow.add_node("promotion", promo_node)
gen_workflow.add_node("review", review_node)
gen_workflow.add_node("increment_count", increment_refinement)

gen_workflow.set_entry_point("content_creation")
gen_workflow.add_edge("content_creation", "promotion")
gen_workflow.add_edge("promotion", "review")

# Conditional Edge
gen_workflow.add_conditional_edges(
    "review",
    should_refine,
    {
        "refine": "increment_count",
        "end": END
    }
)

gen_workflow.add_edge("increment_count", "content_creation")

# Compile Generation Graph
generation_graph = gen_workflow.compile()
