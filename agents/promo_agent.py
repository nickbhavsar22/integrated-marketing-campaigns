from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.state import AgentState
from core.llm import get_llm


class PromotionalAgent:
    def __init__(self):
        self.temperature = 0.5

    def generate_promo(self, asset: dict, brand_voice: str = "", brand_tone: str = "") -> dict:
        """
        Creates promo materials for a generated asset.
        """
        llm = get_llm(temperature=self.temperature)
        content_preview = asset.get("content", "")[:1000]

        brand_block = ""
        if brand_voice or brand_tone:
            brand_block = f"""
            **BRAND VOICE & TONE:**
            - Voice: {brand_voice or 'Not specified'}
            - Tone: {brand_tone or 'Not specified'}
            All promotional copy MUST reflect this voice and tone consistently.
            """

        prompt = ChatPromptTemplate.from_template(
            """
            You are a Social Media & Email Marketing Manager.
            Create promotional copy for the following new piece of content.

            **Content Preview:**
            {content}
            {brand_block}

            **Deliverables:**
            1. **LinkedIn Post:** Hook-driven, professional but conversational, 3 hashtags.
            2. **Email Sequence:** 2-part nurture (Subject Line + Body).
            3. **Ad Copy:**
               - LinkedIn Ad (Hook, Body, CTA).
               - Google Search Ad (Headlines, Descriptions).
               - Meta Ad (Caption, Hook).
            4. **Tweet/X Post:** Punchy, short.

            Output as Markdown.
            """
        )

        chain = prompt | llm | StrOutputParser()
        promo_content = chain.invoke({"content": content_preview, "brand_block": brand_block})

        return {
            "parent_asset_id": asset.get("id"),
            "promo_content": promo_content
        }

    def batch_promote(self, state: AgentState) -> dict:
        """
        Generates promo content for each asset (kept in-memory, no filesystem writes).
        """
        assets = state.get("generated_assets", [])
        errors = state.get("errors", [])
        brand_voice = state.get("brand_voice", "")
        brand_tone = state.get("brand_tone", "")

        for asset in assets:
            try:
                promo = self.generate_promo(asset, brand_voice, brand_tone)
                asset["promotional_materials"] = promo["promo_content"]
            except Exception as e:
                errors.append({
                    "agent_name": "PromotionalAgent",
                    "error_type": "api_error",
                    "message": f"Failed to generate promo for asset '{asset.get('title', 'unknown')}': {str(e)}",
                    "recoverable": True
                })

        return {"generated_assets": assets, "errors": errors}
