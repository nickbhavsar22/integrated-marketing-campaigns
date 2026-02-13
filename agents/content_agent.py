import time
import concurrent.futures
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState
from core.llm import get_llm


class ContentCreatorAgent:
    def __init__(self):
        self.temperature = 0.4

    def generate_asset(self, asset_request: dict, campaign_brief: dict, strategy_framework: str = "", company_name: str = "Company", refinement_instructions: str = "", brand_voice: str = "", brand_tone: str = "") -> dict:
        """
        Generates a single content asset based on the request (row from manifest).
        """
        time.sleep(5)
        llm = get_llm(temperature=self.temperature)

        asset_type = asset_request.get("asset_type", asset_request.get("recommended_asset_type", "Blog Post"))
        jtbd = asset_request.get("jtbd", "")
        question = asset_request.get("burning_question", "")
        persona = asset_request.get("persona_role", "Buyer")

        print(f"Generating {asset_type} for {persona}...")

        refinement_block = ""
        if refinement_instructions:
            refinement_block = f"""
            **REFINEMENT REQUEST:**
            The previous version of this asset was reviewed and requires the following improvements:
            {refinement_instructions}

            Please ensure this new version addresses all the gaps mentioned above while maintaining the original strategic alignment.
            """

        brand_block = ""
        if brand_voice or brand_tone:
            brand_block = f"""
            **BRAND VOICE & TONE:**
            - Voice: {brand_voice or 'Not specified'}
            - Tone: {brand_tone or 'Not specified'}
            All content MUST reflect this voice and tone consistently.
            """

        prompt = ChatPromptTemplate.from_template(
            """
            You are an Expert Content Creator.
            Create a comprehensive {asset_type} for the described campaign.

            **STRATEGIC CONTEXT (STRICTLY ADHERE TO THIS):**
            {strategy}

            **Campaign Brief:**
            {brief}
            {brand_block}

            **Target Persona:** {persona}
            **Job to be Done:** {jtbd}
            **Key Question to Answer:** {question}

            {refinement_block}

            **Requirements:**
            - **Voice & Tone:** MUST match the Positioning and Messaging Pillars defined in the Strategic Context.
            - **Theme:** Reinforce the core campaign theme.
            - **Structure:** Robust header structure, clear takeaways.
            - **Length:** Detailed (approx 800-1000 words).

            Output the content in Markdown format.
            """
        )

        chain = prompt | llm | StrOutputParser()
        content = chain.invoke({
            "asset_type": asset_type,
            "strategy": strategy_framework,
            "brief": str(campaign_brief),
            "persona": persona,
            "jtbd": jtbd,
            "question": question,
            "refinement_block": refinement_block,
            "brand_block": brand_block
        })

        return {
            "type": asset_type,
            "title": f"{asset_type} for {persona}: {question}",
            "content": content,
            "persona": persona,
            "id": asset_request.get("id", str(hash(content)))
        }

    def batch_generate(self, state: AgentState) -> dict:
        """
        Generates assets concurrently using a thread pool.
        """
        manifest = state.get("content_manifest", [])
        brief = state.get("campaign_brief", {})
        strategy = state.get("strategy_framework", "")
        instructions = state.get("refinement_instructions", "")
        company_name = state.get("company_name", "Company")
        brand_voice = state.get("brand_voice", "")
        brand_tone = state.get("brand_tone", "")

        assets = []
        errors = state.get("errors", [])

        # Normalize asset types
        for item in manifest:
            if "asset_type" not in item and "recommended_asset_type" in item:
                item["asset_type"] = item["recommended_asset_type"]
            elif "asset_type" not in item:
                item["asset_type"] = "Blog Post"

        def generate_one(item):
            time.sleep(1)  # Basic rate limiting between thread starts
            return self.generate_asset(item, brief, strategy, company_name, instructions, brand_voice, brand_tone)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(generate_one, item): item for item in manifest}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        assets.append(result)
                except Exception as e:
                    item = futures[future]
                    errors.append({
                        "agent_name": "ContentCreatorAgent",
                        "error_type": "generation_error",
                        "message": f"Failed to generate {item.get('recommended_asset_type', 'asset')}: {str(e)}",
                        "recoverable": True
                    })

        return {"generated_assets": assets, "errors": errors}
