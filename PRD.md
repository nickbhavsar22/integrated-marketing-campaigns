# Product Requirements Document (PRD): Integrated Marketing Campaigns System

## 1. Executive Summary
**Project Name:** Integrated Marketing Campaigns System
**Context:** B2B go-to-market strategies are becoming inefficient due to rising Customer Acquisition Costs (CAC) and the shift in buyer behavior towards LLM-based research. Buyers seek specific solutions tailored to their unique business context, requiring vendors to produce highly targeted content for each member of a buying committee across various buying stages.
**Goal:** Build an AI-powered system that ingests company data, researches the market, and orchestrates the creation of comprehensive, multi-persona, multi-stage marketing campaigns using an Orchestrator-Agent architecture.

## 2. Problem Statement
*   **The Shift:** B2B buyers now use LLMs for deep, contextual research, moving away from generic search queries.
*   **The Need:** Vendors must address specific "Jobs to be Done" (JTBD) for each purchasing decision-maker (Buying Committee) at every stage of their journey.
*   **The Challenge:** Creating this volume of deeply personalized, segment-specific content manually is cost-prohibitive and unscalable, leading to poor retention and high CAC.

## 3. Functional Requirements

### 3.1. Inputs Module
The system must accept the following inputs to ground its generation:
*   **Company URL:** For scraping key pages (Home, About, Product).
*   **Deep Research:** Integrate Google Gemini for broad and very detailed background research on the company.
*   **Context Folder:** A directory for user-uploaded documents (PDFs, PPTs, Docx) containing strategy, brand guidelines, etc.
*   **Brand Aspects:** Explicit inputs for brand voice, tone, and key messaging pillars.

### 3.2. Workflows & Agentic Architecture
The system will utilize an **Orchestrator-Worker** model with specialized agents.

#### Phase 1: Research & Strategy
*   **Company Research Agent:** Analyzes the inputs to understand the company's core identity,  value proposition and market position.
*   **Market & Segment Agent:**
    *   Researches solutions and identifies potential market segments.
    *   Defines the **Buying Committee Personas** (e.g., Champion, Economic Buyer, Technical Evaluator) and identifies their job titles and key pain points by buying stage 
*   **Competitor Agent:** Performs deep competitive analysis and identifies positioning gaps.
*   **Strategy Agent:** Drafts key positioning and messaging frameworks for the selected segments.

#### Phase 2: Campaign Planning
*   **Campaign Architect Agent:**
    *   Selects a target segment.
    *   Defines Campaign Focus & Strategy.
    *   Produces a **Campaign Brief**:
        *   Objectives.
        *   Timeframe & Funnel Stage.
        *   Key Personas.
        *   Campaign Theme.
        *   Messaging adaptation.

#### Phase 3: Content Foundation (The "Brain")
*   **JTBD Analyst:**
    *   Mapping "Jobs to be Done" for each Persona at each Stage.
    *   Develops a **Content Manifest** based on the *questions* buyers ask at every step.

#### Phase 4: Asset Generation
*   **Content Creator Agents:** Generates the actual assets based on the Content Manifest.
    *   *Long-form:* Blogs, eBooks, White Papers.
    *   *Visual/Presentation:* Slide Decks, Infographics (text descriptions/prompts).
    *   *Webinar:* Scripts/Outlines.
    *   *Other:* Consider building out other content asset types that may be relevant to the target audience and campaign goals.
*   **Promotional Agent:** Creates supporting assets for distribution.
    *   Emails (Nurture sequences, blasts).
    *   Ad Copy (LinkedIn, Google, Meta).
    *   Social Posts.

## 4. Technical Recommendations (Tech Stack)

Given the requirements for complex orchestration, deep research, and data handling, the following stack is recommended:

### Core Framework (Backend)
*   **Language:** **Python 3.10+**. Python is the undisputed leader for AI agent development.
*   **Orchestration:** **LangGraph** (preferred) or **LangChain**. LangGraph is ideal for the cyclic, stateful workflows described (Research -> Feedback -> Strategy -> Content).
*   **LLM Interface:**
    *   **Anthropic (Claude 4.5 Opus):** For high-quality reasoning and content generation (Code & Copy).
    *   **Google Gemini 3 Pro:** Specifically for the "Deep Research" requirement (large context window is perfect for ingesting entire websites/books).

### Data & Research
*   **Web Scraping:** **Firecrawl** or **Playwright + BeautifulSoup**. To extract clean markdown from company websites.
*   **Search:** **Tavily API** or **Google Search API**. For competitor and market research.
*   **Document Parsing:** **Unstructured.io** or **PyPDF**. To ingest the "Context Folder" documents.

### Interaction & UI
*   **Interface:** **Streamlit** or **Chainlit**. A chat-based UI is native to this workflow, allowing the user to review "Draft Briefs" or "Persona Profiles" before the agents proceed to the next step (Human-in-the-loop).

### Storage
*   **Local Filesystem:** Markdown files for transparency (easy to read/edit output).
*   **Vector DB (Optional):** **ChromaDB** (local) if the "Context Folder" grows large and requires semantic search.

## 5. Development Roadmap
1.  **Project Setup:** Git, Venv, API Keys.
2.  **Input Ingestion:** Build the scraper and document loader.
3.  **Research Swarm:** Implement the Company, Segment, and Competitor agents.
4.  **Strategy & Brief Module:** Build the logic to synthesize research into a Campaign Brief.
5.  **Content Engine:** Implement the JTBD mapper and Asset Generators.
6.  **CLI/UI:** Wrap in a user-friendly interface.
