# Integrated Marketing Campaigns AI

An AI-powered system that orchestrates the creation of comprehensive, multi-persona, multi-stage marketing campaigns for B2B SaaS companies. Built with LangGraph, Streamlit, and Gemini 2.0 Flash.

## Architecture

```
User Input (URL + Docs + Brand Settings)
    |
    v
[Input Node] --> Scrape website + Load documents
    |
    v
[Research Agent] --> Deep company analysis (Gemini 2.0 Flash)
    |
    v
[Segment Agent] --> Market segments + Buying committee personas
    |
    v
[Competitor Agent] --> Competitive landscape (+ Tavily real-time search)
    |
    v
[Strategy Agent] --> Positioning & messaging framework
    |
    v
[Campaign Agent] --> Structured campaign brief
    |
    v
[JTBD Agent] --> Content manifest with asset recommendations
    |
    v  (user reviews/edits at each stage)
[Content Agent] --> Generate assets (parallel, 3 workers)
    |
    v
[Promo Agent] --> LinkedIn, email, ad copy for each asset
    |
    v
[Reviewer Agent] --> Quality audit (score 0-100)
    |
    v  (auto-refine if score < threshold)
[Export] --> DOCX or Markdown ZIP download
```

## Features

- **Deep Research:** Scrapes company websites and analyzes market position using Gemini 2.0 Flash
- **Strategic Orchestration:** LangGraph workflows manage the full pipeline (Research -> Strategy -> Content)
- **JTBD Content Engine:** Generates personalized assets for each buying committee member
- **Brand Voice Control:** Customize voice, tone, and messaging pillars for all generated content
- **Interactive Editing:** Edit research, strategy, and content at every stage with re-run capability
- **Campaign Save/Load:** Export and import campaign state as JSON for resuming later
- **Quality Auditor:** Reviewer Agent scores outputs against PRD goals with configurable auto-refinement
- **Multiple Exports:** Branded DOCX reports and Markdown ZIP packages
- **Security Hardened:** SSRF protection, file upload sanitization, content length guards

## Project Structure

```
agents/              # 9 specialized AI agents
  research_agent.py  # Company research and analysis
  segment_agent.py   # Market segmentation and personas
  competitor_agent.py # Competitive analysis (+ Tavily)
  strategy_agent.py  # Positioning and messaging
  campaign_agent.py  # Campaign brief creation
  jtbd_agent.py      # Jobs-to-be-Done mapping
  content_agent.py   # Content generation (parallel)
  promo_agent.py     # Promotional materials
  reviewer_agent.py  # Quality audit and scoring
core/
  state.py           # AgentState TypedDict (shared workflow state)
  graph.py           # LangGraph workflow definitions
ui/
  app.py             # Streamlit web interface
utils/
  scraper.py         # Web scraper with SSRF protection
  doc_loader.py      # PDF/DOCX/TXT document loader
  docx_generator.py  # Branded Word document generator
.streamlit/
  config.toml        # Streamlit theme and server config
```

## Prerequisites

- Python 3.10+
- Google API key (Gemini 2.0 Flash) - **required**
- Anthropic API key - optional
- Tavily API key - optional (enables real-time competitor search)

## Local Setup

1. **Clone and create virtual environment:**
   ```bash
   git clone <repo-url>
   cd integrated-marketing-campaigns
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:** Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_key
   ANTHROPIC_API_KEY=your_anthropic_key
   TAVILY_API_KEY=your_tavily_key
   ```

3. **Run the app:**
   ```bash
   streamlit run ui/app.py
   ```

## Streamlit Cloud Deployment

1. Push the code to a GitHub repository (ensure `.env` is in `.gitignore`)
2. Connect the repo to [Streamlit Cloud](https://share.streamlit.io/)
3. Set the main file path to `ui/app.py`
4. Add secrets in **Settings > Secrets**:
   ```toml
   GOOGLE_API_KEY = "your_gemini_key"
   ANTHROPIC_API_KEY = "your_anthropic_key"
   TAVILY_API_KEY = "your_tavily_key"
   ```
5. Enable **Viewer Authentication** (Google SSO) in app settings to restrict access
6. The app will auto-detect the cloud environment and use these secrets

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key for all LLM operations |
| `ANTHROPIC_API_KEY` | No | Anthropic Claude key (for future model flexibility) |
| `TAVILY_API_KEY` | No | Tavily search key for real-time competitor research |
| `GOOGLE_MODEL` | No | Override default model (default: `gemini-2.0-flash`) |

## Documentation

- [PRD.md](PRD.md) - Product requirements and architecture goals
- [CLAUDE.md](CLAUDE.md) - WAT Framework instructions and project conventions
