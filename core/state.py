from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # Inputs
    company_name: str
    company_url: str
    uploaded_files: List[str]
    
    # Raw Data
    raw_web_content: str
    raw_doc_content: str
    
    # Analysis Outputs
    deep_research: str
    segments: List[Dict[str, Any]]
    personas: List[Dict[str, Any]]
    competitor_analysis: str
    strategy_framework: str
    
    # Campaign
    campaign_brief: Dict[str, Any]
    content_manifest: List[Dict[str, Any]]
    generated_assets: List[Dict[str, Any]]
    
    # Review & Refinement
    reviewer_feedback: Optional[str]
    reviewer_score: Optional[int]
    refinement_instructions: Optional[str]
    refinement_count: int

    # Brand Customization
    brand_voice: str          # e.g. "Authoritative, technical, precise"
    brand_tone: str           # e.g. "Professional", "Conversational", "Technical"
    messaging_pillars: List[str]  # Key messaging themes

    # Error Tracking
    errors: List[Dict[str, Any]]  # [{agent_name, error_type, message, recoverable}]

    # Configurable Settings
    refinement_threshold: int  # Quality score threshold (default 80)
    max_refinements: int       # Max refinement loops (default 2)

    # Messages for chat history if needed
    messages: List[BaseMessage]
