import json
import io
import re
import os
import zipfile
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
MAX_FILE_SIZE_MB = 10


def sanitize_filename(name):
    """Sanitize uploaded filename to prevent path traversal."""
    # Strip directory separators
    name = name.replace("/", "").replace("\\", "")
    # Strip leading dots
    name = name.lstrip(".")
    # Keep only safe characters
    name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", name)
    # Limit length
    return name[:255] if name else "unnamed_file"


def safe_markdown(content, max_length=100000):
    """Safely render markdown with length guard."""
    if not content:
        return
    content = str(content)
    if len(content) > max_length:
        st.markdown(content[:max_length])
        st.warning(f"Content truncated (showing {max_length:,} of {len(content):,} characters)")
    else:
        st.markdown(content)


# ---------------------------------------------------------------------------
# Environment & Secrets
# ---------------------------------------------------------------------------

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Secret Handling for Cloud vs Local
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    if "TAVILY_API_KEY" in st.secrets:
        os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
except FileNotFoundError:
    pass  # No secrets.toml -- fall through to .env loading below

# Load env locally (explicit path to ensure it is found)
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)


# ---------------------------------------------------------------------------
# Page config & title
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Integrated Marketing Campaigns", layout="wide", page_icon="IMC")

results = st.session_state.get("workflow_results", {})
extracted_name = results.get("company_name")

if extracted_name:
    st.title(f"Marketing Strategy: {extracted_name}")
else:
    st.title("Integrated Marketing Campaigns AI")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Project Inputs")
    company_url = st.text_input("Company URL", placeholder="https://example.com")

    uploaded_files = st.file_uploader(
        "Upload Context Documents",
        accept_multiple_files=True,
        type=["pdf", "docx", "doc", "txt", "md"],
    )

    st.divider()
    st.header("Brand Settings")
    brand_voice = st.text_input(
        "Brand Voice",
        placeholder="e.g., Authoritative, technical, precise",
        help="Describe how the brand should sound",
    )
    brand_tone = st.selectbox(
        "Brand Tone",
        ["Professional", "Conversational", "Technical", "Bold", "Empathetic"],
        help="Select the overall tone for content",
    )
    messaging_pillars_text = st.text_area(
        "Key Messaging Pillars",
        placeholder="Speed\nSecurity\nScale",
        help="One pillar per line",
    )
    messaging_pillars = (
        [p.strip() for p in messaging_pillars_text.split("\n") if p.strip()]
        if messaging_pillars_text
        else []
    )

    with st.expander("Advanced Settings"):
        refinement_threshold = st.slider(
            "Quality Threshold", 50, 100, 80, help="Minimum reviewer score before accepting"
        )
        max_refinements = st.number_input(
            "Max Refinement Loops", 0, 5, 2, help="How many times to auto-refine content"
        )

    st.divider()
    st.header("Campaign State")

    # Save campaign state
    if st.session_state.get("workflow_results"):
        campaign_json = json.dumps(st.session_state["workflow_results"], default=str, indent=2)
        st.download_button(
            label="Export Campaign State",
            data=campaign_json,
            file_name=f"campaign_{st.session_state['workflow_results'].get('company_name', 'draft')}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )

    # Load campaign state
    loaded_state = st.file_uploader("Import Campaign State", type=["json"], key="state_loader")
    if loaded_state:
        try:
            imported = json.loads(loaded_state.read())
            st.session_state["workflow_results"] = imported
            st.success("Campaign state loaded!")
            st.rerun()
        except json.JSONDecodeError:
            st.error("Invalid JSON file")


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(["Research", "Strategy", "Campaign Brief", "Content Assets"])

if "workflow_results" not in st.session_state:
    st.session_state["workflow_results"] = {}


# ---------------------------------------------------------------------------
# Tab 1 -- Research
# ---------------------------------------------------------------------------

with tab1:
    st.header("Deep Research")

    if "edit_research" not in st.session_state:
        st.session_state["edit_research"] = False

    if st.button("Start Research Phase", key="start_research"):
        if not company_url:
            st.error("Please provide a Company URL.")
        else:
            with st.status("Running Research Phase...", expanded=True) as status:
                try:
                    from core.graph import (
                        input_node,
                        research_node,
                        segment_node,
                        competitor_node,
                        strategy_node,
                        campaign_node,
                        jtbd_node,
                    )

                    # Handle file uploads - store in session as bytes
                    uploaded_file_data = []
                    if uploaded_files:
                        for uf in uploaded_files:
                            if uf.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                                st.warning(f"Skipping {uf.name}: exceeds {MAX_FILE_SIZE_MB}MB limit")
                                continue
                            safe_name = sanitize_filename(uf.name)
                            ext = os.path.splitext(safe_name)[1].lower()
                            if ext not in ALLOWED_EXTENSIONS:
                                st.warning(f"Skipping {uf.name}: unsupported file type")
                                continue
                            uploaded_file_data.append((safe_name, uf.getvalue()))
                        st.info(f"Loaded {len(uploaded_file_data)} documents for context.")

                    # Build initial state
                    current_state = {
                        "company_url": company_url,
                        "uploaded_files": [f[0] for f in uploaded_file_data],
                        "uploaded_file_bytes": uploaded_file_data,
                        "brand_voice": brand_voice,
                        "brand_tone": brand_tone,
                        "messaging_pillars": messaging_pillars,
                        "refinement_threshold": refinement_threshold,
                        "max_refinements": max_refinements,
                        "errors": [],
                    }

                    # Step-by-step execution with progress
                    st.write("Scraping company website...")
                    result = input_node(current_state)
                    current_state.update(result)

                    st.write("Analyzing company identity and value proposition...")
                    result = research_node(current_state)
                    current_state.update(result)

                    st.write("Identifying market segments and personas...")
                    result = segment_node(current_state)
                    current_state.update(result)

                    st.write("Analyzing competitive landscape...")
                    result = competitor_node(current_state)
                    current_state.update(result)

                    st.write("Developing positioning and messaging strategy...")
                    result = strategy_node(current_state)
                    current_state.update(result)

                    st.write("Creating campaign brief...")
                    result = campaign_node(current_state)
                    current_state.update(result)

                    st.write("Mapping Jobs-to-be-Done and content plan...")
                    result = jtbd_node(current_state)
                    current_state.update(result)

                    st.session_state["workflow_results"] = current_state
                    status.update(label="Research Complete!", state="complete")

                    # Show any errors
                    for err in current_state.get("errors", []):
                        st.warning(f"[{err['agent_name']}] {err['message']}")

                    st.rerun()
                except Exception as e:
                    status.update(label="Research Failed", state="error")
                    st.error(f"Error: {e}")

    # Re-run individual stages
    results = st.session_state.get("workflow_results", {})
    if results.get("deep_research"):
        col_rerun1, col_rerun2, _ = st.columns([1, 1, 3])
        with col_rerun1:
            if st.button("Re-run Research", key="rerun_research"):
                with st.spinner("Re-analyzing..."):
                    from core.graph import research_node

                    result = research_node(results)
                    st.session_state["workflow_results"].update(result)
                    st.rerun()
        with col_rerun2:
            if st.button("Re-run Competitors", key="rerun_competitors"):
                with st.spinner("Re-analyzing competitors..."):
                    from core.graph import competitor_node

                    result = competitor_node(results)
                    st.session_state["workflow_results"].update(result)
                    st.rerun()

    # Display Results
    research_content = results.get("deep_research", "")
    competitor_table = results.get("competitor_analysis", "")

    if research_content:
        lines = research_content.split("\n")
        cleaned_lines = [
            line
            for line in lines
            if not line.strip().startswith(("Analyst:", "Source Data:", "Focus:"))
        ]
        clean_research = "\n".join(cleaned_lines)

        full_report = clean_research
        if competitor_table:
            full_report += "\n\n## 5. Competitive Positioning Analysis\n" + competitor_table

        st.subheader(f"Company Analysis: {results.get('company_name', '')}")

        if st.session_state["edit_research"]:
            updated_report = st.text_area(
                "Edit Research Report", value=full_report, height=800, key="research_editor"
            )
            col_save, col_cancel = st.columns([1, 4])
            with col_save:
                if st.button("Save Report", key="save_research"):
                    st.session_state["workflow_results"]["deep_research"] = updated_report
                    st.session_state["workflow_results"]["competitor_analysis"] = ""
                    st.session_state["edit_research"] = False
                    st.rerun()
            with col_cancel:
                if st.button("Cancel", key="cancel_research"):
                    st.session_state["edit_research"] = False
                    st.rerun()
        else:
            safe_markdown(full_report)
            st.caption("Review the full report above. Click edit to refine.")
            if st.button("Edit Report", key="edit_research_btn"):
                st.session_state["edit_research"] = True
                st.rerun()


# ---------------------------------------------------------------------------
# Tab 2 -- Strategy & Segmentation
# ---------------------------------------------------------------------------

with tab2:
    st.header("Strategy & Segmentation")
    results = st.session_state.get("workflow_results", {})

    if "edit_strategy" not in st.session_state:
        st.session_state["edit_strategy"] = False

    # Re-run buttons
    if results.get("deep_research"):
        col_r1, col_r2, _ = st.columns([1, 1, 3])
        with col_r1:
            if st.button("Re-run Segmentation", key="rerun_segmentation"):
                with st.spinner("Re-analyzing segments..."):
                    from core.graph import segment_node

                    result = segment_node(results)
                    st.session_state["workflow_results"].update(result)
                    st.rerun()
        with col_r2:
            if st.button("Re-run Strategy", key="rerun_strategy"):
                with st.spinner("Re-developing strategy..."):
                    from core.graph import strategy_node

                    result = strategy_node(results)
                    st.session_state["workflow_results"].update(result)
                    st.rerun()

    # Segments display
    if results.get("segments"):
        st.subheader("Target Segments")
        for seg in results["segments"]:
            st.markdown(f"**{seg.get('name')}**: {seg.get('rationale')}")

    # Personas display
    if results.get("personas"):
        st.subheader("Buying Committee")
        for p in results["personas"]:
            with st.expander(f"{p.get('role')} ({p.get('type')})"):
                st.write(f"**JTBD:** {p.get('job_to_be_done')}")
                st.write(f"**Pains:** {', '.join(p.get('pain_points', []))}")

    st.divider()

    # Strategy framework with edit mode
    if results.get("strategy_framework"):
        st.subheader("Strategy Framework")
        current_strategy = results["strategy_framework"]

        if st.session_state["edit_strategy"]:
            updated_strategy = st.text_area(
                "Edit Strategy Content", value=current_strategy, height=600, key="strategy_editor"
            )
            col_save, col_cancel = st.columns([1, 4])
            with col_save:
                if st.button("Save Strategy", key="save_strategy"):
                    st.session_state["workflow_results"]["strategy_framework"] = updated_strategy
                    st.session_state["edit_strategy"] = False
                    st.rerun()
            with col_cancel:
                if st.button("Cancel", key="cancel_strategy"):
                    st.session_state["edit_strategy"] = False
                    st.rerun()
        else:
            safe_markdown(current_strategy)
            st.caption("Review the strategy above. Click edit to make changes.")
            if st.button("Edit Strategy", key="edit_strategy_btn"):
                st.session_state["edit_strategy"] = True
                st.rerun()


# ---------------------------------------------------------------------------
# Tab 3 -- Campaign Brief
# ---------------------------------------------------------------------------

with tab3:
    st.header("Campaign Brief")
    results = st.session_state.get("workflow_results", {})
    brief = results.get("campaign_brief")

    if "edit_brief" not in st.session_state:
        st.session_state["edit_brief"] = False

    # Re-run button
    if results.get("strategy_framework"):
        if st.button("Re-run Campaign Brief", key="rerun_brief"):
            with st.spinner("Re-creating campaign brief..."):
                from core.graph import campaign_node

                result = campaign_node(results)
                st.session_state["workflow_results"].update(result)
                st.rerun()

    if brief:
        brief_text = ""
        if isinstance(brief, dict):
            lines = []
            for k, v in brief.items():
                display_key = k.replace("_", " ").title()
                val_str = ", ".join(v) if isinstance(v, list) else str(v)
                lines.append(f"**{display_key}**: {val_str}")
            brief_text = "\n\n".join(lines)
        else:
            brief_text = str(brief)

        st.subheader("Campaign Brief Details")

        if st.session_state["edit_brief"]:
            updated_brief = st.text_area(
                "Edit Brief Content", value=brief_text, height=500, key="brief_editor"
            )
            col_save, col_cancel = st.columns([1, 4])
            with col_save:
                if st.button("Save Brief", key="save_brief"):
                    st.session_state["workflow_results"]["campaign_brief"] = updated_brief
                    st.session_state["edit_brief"] = False
                    st.rerun()
            with col_cancel:
                if st.button("Cancel", key="cancel_brief"):
                    st.session_state["edit_brief"] = False
                    st.rerun()
        else:
            safe_markdown(brief_text)
            st.caption("Review the brief above. Click edit to make changes.")
            if st.button("Edit Brief", key="edit_brief_btn"):
                st.session_state["edit_brief"] = True
                st.rerun()
    else:
        st.info("Run Research first to generate a campaign brief.")


# ---------------------------------------------------------------------------
# Tab 4 -- Content Assets
# ---------------------------------------------------------------------------

with tab4:
    st.header("Content & JTBD Manifest")
    results = st.session_state.get("workflow_results", {})
    manifest = results.get("content_manifest", [])
    assets = results.get("generated_assets", [])

    if manifest:
        st.subheader("Content Plan")
        st.info("Select assets to generate and customize the type for each.")

        # Asset type options
        type_options = [
            "Blog Post",
            "LinkedIn Post",
            "Email Sequence",
            "Whitepaper",
            "Case Study",
            "Webinar Script",
            "Landing Page",
        ]

        # Initialize selection state
        if "manifest_selections" not in st.session_state:
            st.session_state["manifest_selections"] = {i: True for i in range(len(manifest))}

        # Bulk buttons
        col_all, col_none, col_count, _ = st.columns([1, 1, 2, 3])
        with col_all:
            if st.button("Select All", key="select_all"):
                st.session_state["manifest_selections"] = {i: True for i in range(len(manifest))}
                st.rerun()
        with col_none:
            if st.button("Deselect All", key="deselect_all"):
                st.session_state["manifest_selections"] = {i: False for i in range(len(manifest))}
                st.rerun()
        with col_count:
            selected_count = sum(1 for v in st.session_state["manifest_selections"].values() if v)
            st.write(f"**{selected_count} of {len(manifest)} selected**")

        # Card-based manifest editor
        for i, item in enumerate(manifest):
            # Normalize asset type
            raw_type = str(
                item.get("recommended_asset_type", item.get("asset_type", "Blog Post"))
            )
            if raw_type not in type_options:
                if "whitepaper" in raw_type.lower():
                    raw_type = "Whitepaper"
                elif "linkedin" in raw_type.lower():
                    raw_type = "LinkedIn Post"
                elif "email" in raw_type.lower():
                    raw_type = "Email Sequence"
                elif "blog" in raw_type.lower():
                    raw_type = "Blog Post"
                elif "webinar" in raw_type.lower():
                    raw_type = "Webinar Script"
                elif "case" in raw_type.lower():
                    raw_type = "Case Study"
                elif "landing" in raw_type.lower():
                    raw_type = "Landing Page"
                else:
                    raw_type = "Blog Post"

            with st.container(border=True):
                col_check, col_persona, col_type = st.columns([0.5, 3, 2])

                with col_check:
                    selected = st.checkbox(
                        "Gen",
                        value=st.session_state["manifest_selections"].get(i, True),
                        key=f"sel_{i}",
                        label_visibility="collapsed",
                    )
                    st.session_state["manifest_selections"][i] = selected

                with col_persona:
                    st.markdown(f"**{item.get('persona_role', 'Unknown')}**")
                    st.caption(item.get("jtbd", ""))

                with col_type:
                    new_type = st.selectbox(
                        "Asset Type",
                        options=type_options,
                        index=type_options.index(raw_type) if raw_type in type_options else 0,
                        key=f"type_{i}",
                        label_visibility="collapsed",
                    )
                    # Update manifest with user selection
                    manifest[i]["recommended_asset_type"] = new_type
                    manifest[i]["asset_type"] = new_type

                # Show burning question
                if item.get("burning_question"):
                    st.caption(f"Key Question: {item['burning_question']}")

        # Update manifest in session state
        st.session_state["workflow_results"]["content_manifest"] = manifest

        # Add custom asset
        with st.expander("Add Custom Asset"):
            custom_persona = st.text_input("Persona Role", key="custom_persona")
            custom_jtbd = st.text_input("Job to be Done", key="custom_jtbd")
            custom_question = st.text_input("Key Question", key="custom_question")
            custom_type = st.selectbox("Asset Type", type_options, key="custom_type")
            if st.button("Add to Plan", key="add_custom"):
                if custom_persona and custom_jtbd:
                    new_item = {
                        "persona_role": custom_persona,
                        "jtbd": custom_jtbd,
                        "burning_question": custom_question,
                        "recommended_asset_type": custom_type,
                        "asset_type": custom_type,
                    }
                    st.session_state["workflow_results"]["content_manifest"].append(new_item)
                    st.session_state["manifest_selections"][len(manifest)] = True
                    st.success("Asset added!")
                    st.rerun()
                else:
                    st.warning("Persona and JTBD are required.")

        # Generate button
        if st.button("Generate Selected Assets", type="primary", key="generate_assets"):
            # Build approved list
            approved_data = []
            current_manifest = st.session_state["workflow_results"].get("content_manifest", [])
            for i, item in enumerate(current_manifest):
                if st.session_state["manifest_selections"].get(i, False):
                    approved_data.append(item)

            if not approved_data:
                st.warning("No assets selected!")
            else:
                with st.status(
                    f"Generating {len(approved_data)} assets...", expanded=True
                ) as gen_status:
                    try:
                        from core.graph import (
                            content_node,
                            promo_node,
                            review_node,
                            should_refine,
                            increment_refinement,
                        )

                        gen_state = {
                            "content_manifest": approved_data,
                            "campaign_brief": results.get("campaign_brief", {}),
                            "strategy_framework": results.get("strategy_framework", ""),
                            "company_name": results.get("company_name", "Company"),
                            "brand_voice": results.get("brand_voice", brand_voice),
                            "brand_tone": results.get("brand_tone", brand_tone),
                            "messaging_pillars": results.get("messaging_pillars", messaging_pillars),
                            "generated_assets": [],
                            "refinement_count": 0,
                            "refinement_instructions": "",
                            "refinement_threshold": refinement_threshold,
                            "max_refinements": max_refinements,
                            "errors": [],
                        }

                        st.write(f"Creating {len(approved_data)} content assets...")
                        result = content_node(gen_state)
                        gen_state.update(result)

                        st.write("Generating promotional materials...")
                        result = promo_node(gen_state)
                        gen_state.update(result)

                        st.write("Running quality review...")
                        result = review_node(gen_state)
                        gen_state.update(result)

                        # Refinement loop
                        while should_refine(gen_state) == "refine":
                            gen_state.update(increment_refinement(gen_state))
                            count = gen_state.get("refinement_count", 0)
                            st.write(f"Refining content (round {count})...")
                            result = content_node(gen_state)
                            gen_state.update(result)
                            result = promo_node(gen_state)
                            gen_state.update(result)
                            st.write(f"Re-reviewing (round {count})...")
                            result = review_node(gen_state)
                            gen_state.update(result)

                        # Merge results
                        st.session_state["workflow_results"]["generated_assets"] = gen_state.get(
                            "generated_assets", []
                        )
                        st.session_state["workflow_results"]["reviewer_feedback"] = gen_state.get(
                            "reviewer_feedback", ""
                        )
                        st.session_state["workflow_results"]["reviewer_score"] = gen_state.get(
                            "reviewer_score", 0
                        )
                        st.session_state["workflow_results"]["refinement_count"] = gen_state.get(
                            "refinement_count", 0
                        )

                        score = gen_state.get("reviewer_score", 0)
                        refinements = gen_state.get("refinement_count", 0)
                        gen_status.update(
                            label=f"Complete! Score: {score}/100 ({refinements} refinement{'s' if refinements != 1 else ''})",
                            state="complete",
                        )

                        for err in gen_state.get("errors", []):
                            st.warning(f"[{err['agent_name']}] {err['message']}")

                        st.rerun()
                    except Exception as e:
                        gen_status.update(label="Generation Failed", state="error")
                        st.error(f"Error: {e}")

    else:
        if results.get("campaign_brief"):
            st.warning("Content plan not generated yet.")
        else:
            st.info("Run Research first to create a content plan.")

    # Regenerate JTBD
    if results.get("campaign_brief"):
        if st.button("Regenerate Content Plan", key="regen_plan"):
            with st.spinner("Re-planning content mix..."):
                try:
                    from core.graph import jtbd_node

                    current_state = {
                        "campaign_brief": results.get("campaign_brief"),
                        "personas": results.get("personas"),
                        "strategy_framework": results.get("strategy_framework"),
                    }
                    new_manifest = jtbd_node(current_state)
                    st.session_state["workflow_results"]["content_manifest"] = new_manifest.get(
                        "content_manifest", []
                    )
                    st.session_state["manifest_selections"] = {
                        i: True
                        for i in range(len(new_manifest.get("content_manifest", [])))
                    }
                    st.success("Content plan updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # Export section
    assets = st.session_state.get("workflow_results", {}).get("generated_assets", [])
    if assets:
        st.divider()
        st.subheader("Export Campaign")

        export_format = st.selectbox(
            "Export Format", ["Word (DOCX)", "Markdown (ZIP)"], key="export_format"
        )

        if export_format == "Word (DOCX)":
            if st.button("Generate DOCX Report", key="gen_docx"):
                with st.spinner("Compiling report..."):
                    try:
                        from utils.docx_generator import generate_campaign_docx_bytes

                        company_name = results.get("company_name", "Campaign")
                        company_slug = re.sub(r"[^a-zA-Z0-9_]", "_", company_name)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        docx_filename = f"{company_slug}_Strategy_{timestamp}.docx"

                        buf = generate_campaign_docx_bytes(results)
                        st.download_button(
                            label="Download DOCX Report",
                            data=buf,
                            file_name=docx_filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="dl_docx",
                        )
                    except Exception as e:
                        st.error(f"Export error: {e}")

        elif export_format == "Markdown (ZIP)":
            if st.button("Generate Markdown ZIP", key="gen_zip"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, asset in enumerate(assets):
                        title = re.sub(r"[^a-zA-Z0-9_]", "_", asset.get("title", f"asset_{i}"))
                        content = asset.get("content", "")
                        promo = asset.get("promotional_materials", "")
                        full_content = content
                        if promo:
                            full_content += f"\n\n---\n\n## Promotional Materials\n\n{promo}"
                        zf.writestr(f"{title}.md", full_content)

                zip_buffer.seek(0)
                st.download_button(
                    label="Download Markdown ZIP",
                    data=zip_buffer,
                    file_name=f"campaign_assets_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    key="dl_zip",
                )

        # Reviewer feedback
        if results.get("reviewer_feedback"):
            with st.expander("Quality Review"):
                score = results.get("reviewer_score", 0)
                st.metric("Campaign Score", f"{score}/100")
                safe_markdown(results["reviewer_feedback"])

        st.divider()
        st.header("Generated Content Library")

        # Side-by-side content display
        for i, asset in enumerate(assets):
            asset_id = asset.get("id", str(i))
            title = asset.get("title", f"Asset {i + 1}")
            asset_type = asset.get("type", "Content")

            with st.expander(f"{asset_type} | {title}", expanded=(i == 0)):
                # Initialize edit state for this asset
                edit_key = f"edit_asset_{asset_id}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                if st.session_state[edit_key]:
                    # Edit mode
                    updated_content = st.text_area(
                        "Edit Content",
                        value=asset.get("content", ""),
                        height=400,
                        key=f"editor_{asset_id}",
                    )
                    col_s, col_c = st.columns([1, 4])
                    with col_s:
                        if st.button("Save", key=f"save_{asset_id}"):
                            st.session_state["workflow_results"]["generated_assets"][i][
                                "content"
                            ] = updated_content
                            st.session_state[edit_key] = False
                            st.rerun()
                    with col_c:
                        if st.button("Cancel", key=f"cancel_{asset_id}"):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    # Side-by-side view
                    col_content, col_promo = st.columns(2)

                    with col_content:
                        st.subheader("Content")
                        safe_markdown(asset.get("content", ""))

                        col_edit, col_dl = st.columns(2)
                        with col_edit:
                            if st.button("Edit", key=f"edit_btn_{asset_id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col_dl:
                            st.download_button(
                                label="Download MD",
                                data=asset.get("content", ""),
                                file_name=f"{asset_type}_{asset_id}.md",
                                mime="text/markdown",
                                key=f"dl_{asset_id}",
                            )

                    with col_promo:
                        st.subheader("Promotional Materials")
                        safe_markdown(
                            asset.get(
                                "promotional_materials", "No promotional materials generated."
                            )
                        )
