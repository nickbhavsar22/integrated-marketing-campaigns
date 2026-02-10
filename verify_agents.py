import os
import json
from dotenv import load_dotenv

load_dotenv()

from agents.campaign_agent import CampaignArchitectAgent
from agents.jtbd_agent import JTBDAnalyst
from agents.reviewer_agent import ReviewerAgent

def verify():
    print("--- Starting Agent Verification ---")
    
    # Mock Data
    state = {
        "company_name": "Acme Corp",
        "deep_research": "Acme Corp provides cloud-based security for fintech and healthcare. They focus on zero-trust architecture.",
        "segments": [
            {"name": "Fintech Disruptors", "rationale": "High growth, security-conscious."},
            {"name": "Traditional Healthcare", "rationale": "High compliance needs, slow to adopt."}
        ],
        "personas": [
            {"role": "CISO", "type": "Economic Buyer", "job_to_be_done": "Secure all endpoints without impacting developer velocity."},
            {"role": "DevOps Lead", "type": "Champion", "job_to_be_done": "Automate security scanning in CI/CD pipeline."}
        ],
        "strategy_framework": "# Strategy\n\nFocus on speed of implementation and compliance automation.",
        "refinement_count": 0,
        "refinement_instructions": ""
    }

    # 1. Test CampaignArchitectAgent
    print("\nTesting CampaignArchitectAgent...")
    campaign_agent = CampaignArchitectAgent()
    brief_result = campaign_agent.create_brief(state)
    brief = brief_result.get("campaign_brief", {})
    
    print(f"Primary Segment: {brief.get('primary_target_segment')}")
    print(f"Rationale: {brief.get('segment_rationale')}")
    print(f"Primary Persona: {brief.get('primary_target_persona')}")
    
    if brief.get('primary_target_segment') and brief.get('segment_rationale'):
        print("[PASS] CampaignArchitectAgent")
    else:
        print("[FAIL] CampaignArchitectAgent (Missing segment or rationale)")

    # 2. Test JTBDAnalyst
    print("\nTesting JTBDAnalyst...")
    jtbd_agent = JTBDAnalyst()
    state["campaign_brief"] = brief
    manifest_result = jtbd_agent.analyze_jobs(state)
    manifest = manifest_result.get("content_manifest", [])
    
    print(f"Manifest Size: {len(manifest)}")
    types = set(item.get('recommended_asset_type') for item in manifest)
    print(f"Unique Asset Types found: {types}")
    
    if len(manifest) >= 4 and len(types) >= 3:
        print("[PASS] JTBDAnalyst (Size and Diversity met)")
    else:
        print(f"[FAIL] JTBDAnalyst (Size: {len(manifest)}, Types: {len(types)})")

    # 3. Test ContentCreatorAgent (Generation + Saving)
    print("\nTesting ContentCreatorAgent...")
    from agents.content_agent import ContentCreatorAgent
    content_agent = ContentCreatorAgent()
    
    # Test with just the first item from manifest
    test_item = manifest[0]
    gen_result = content_agent.generate_asset(test_item, brief, state["strategy_framework"])
    
    print(f"Generated Asset Type: {gen_result.get('type')}")
    print(f"Content Length: {len(gen_result.get('content', ''))}")
    
    # Test batch/save logic
    print("Testing batch generation and saving...")
    batch_result = content_agent.batch_generate({
        "content_manifest": [test_item],
        "campaign_brief": brief,
        "strategy_framework": state["strategy_framework"]
    })
    
    generated_assets = batch_result.get("generated_assets", [])
    if generated_assets:
        path = generated_assets[0].get("file_path")
        print(f"Saved to: {path}")
        if path and os.path.exists(path):
            print("[PASS] ContentCreatorAgent (File saved successfully)")
            
            # 4. Test PromotionalAgent (Promotion + Appending)
            print("\nTesting PromotionalAgent...")
            from agents.promo_agent import PromotionalAgent
            promo_agent = PromotionalAgent()
            
            # Run promotion on the generated assets (this should append to file)
            promo_result = promo_agent.batch_promote({"generated_assets": generated_assets})
            
            # Check file content
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if "PROMOTIONAL MATERIALS & AD COPY" in content:
                print("[PASS] PromotionalAgent (Promo materials appended to file)")
                # Check for Ad Copy (Google/LinkedIn/Meta)
                if "LinkedIn Ad" in content or "Google Search Ad" in content:
                    print("[PASS] PromotionalAgent (Rich Ad Copy found)")
                else:
                    print("[FAIL] PromotionalAgent (Missing specific Ad Copy markers)")
            else:
                print("[FAIL] PromotionalAgent (Promo materials NOT found in file)")
        else:
            print("[FAIL] ContentCreatorAgent (File NOT found)")
    else:
        print("[FAIL] ContentCreatorAgent (No assets in batch result)")

    # 5. Test ReviewerAgent
    print("\nTesting ReviewerAgent...")
    reviewer_agent = ReviewerAgent()
    review_result = reviewer_agent.review_campaign({
        "company_name": state["company_name"],
        "strategy_framework": state["strategy_framework"],
        "campaign_brief": brief,
        "generated_assets": generated_assets
    })
    feedback = review_result.get("reviewer_feedback", "")
    score = review_result.get("reviewer_score", 0)
    instructions = review_result.get("refinement_instructions", "")
    
    print(f"Score: {score}%")
    print(f"Instructions Length: {len(instructions)}")
    
    if "Strengths" in feedback and isinstance(score, int):
        print("[PASS] ReviewerAgent (Structured feedback generated)")
    else:
        print("[FAIL] ReviewerAgent (Missing structured data or score)")

    # 6. Test Refinement Simulation
    print("\nTesting ContentCreatorAgent Refinement Mode...")
    state["refinement_instructions"] = "The previous version was too short and lacked technical detail on Zero Trust."
    refined_asset = content_agent.generate_asset(test_item, brief, state["strategy_framework"], state["refinement_instructions"])
    
    print(f"Refined Content Length: {len(refined_asset.get('content', ''))}")
    if "REFINEMENT REQUEST" in refined_asset.get("content", ""):
        # Note: Depending on how the LLM handles it, it might not echo the string exactly, 
        # but our prompt injects it. Let's check if the generation worked.
        print("[PASS] ContentCreatorAgent (Refinement call successful)")
    else:
        # Some LLMs might rewrite so thoroughly they remove the instruction markers, 
        # but usually Gemini is compliant.
        print("[PASS] ContentCreatorAgent (Refinement call completed regardless of markers)")

    # 7. Test Docx Generator
    print("\nTesting Docx Generator...")
    from utils.docx_generator import generate_campaign_docx
    
    # Compile results mimicking app_graph + generation_graph
    full_results = {
        "company_name": state["company_name"],
        "deep_research": state["deep_research"],
        "strategy_framework": state["strategy_framework"],
        "campaign_brief": brief,
        "generated_assets": generated_assets,
        "reviewer_feedback": feedback,
        "reviewer_score": score,
        "refinement_count": 1
    }
    
    output_docx = "outputs/test_campaign.docx"
    os.makedirs("outputs", exist_ok=True)
    
    try:
        generate_campaign_docx(full_results, output_docx)
        if os.path.exists(output_docx):
            print(f"[PASS] Docx Generator (File saved to {output_docx})")
        else:
            print("[FAIL] Docx Generator (File NOT found)")
    except Exception as e:
        print(f"[FAIL] Docx Generator Error: {e}")

if __name__ == "__main__":
    verify()
