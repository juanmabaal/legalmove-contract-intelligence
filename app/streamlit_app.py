import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.config.settings import OUTPUT_DIR
from src.graph.graph_builder import (
    run_contextualization_graph,
    run_extraction_graph,
    run_image_parsing_graph,
)
from src.observability.tracing import get_observability_status


DATA_DIR = PROJECT_ROOT / "data" / "test_contracts"
RUNTIME_UPLOAD_DIR = OUTPUT_DIR / "runtime_uploads"
STREAMLIT_OUTPUT_DIR = OUTPUT_DIR / "streamlit"


SAMPLE_CASES = {
    "generate_case": {
        "label": "Generated Consulting Agreement",
        "original": DATA_DIR / "generate_case" / "original_contract.png",
        "amendment": DATA_DIR / "generate_case" / "amendment.png",
    },
    "simple_case": {
        "label": "Simple Software License Case",
        "original": DATA_DIR / "simple_case" / "original_contract.jpg",
        "amendment": DATA_DIR / "simple_case" / "amendment.jpg",
    },
    "complex_case": {
        "label": "Complex Consulting Case",
        "original": DATA_DIR / "complex_case" / "original_contract.jpg",
        "amendment": DATA_DIR / "complex_case" / "amendment.jpg",
    },
}


def initialize_state() -> None:
    defaults = {
        "analysis_output": None,
        "analysis_case_id": None,
        "analysis_pipeline": None,
        "analysis_started_at": None,
        "analysis_finished_at": None,
        "saved_output_path": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    for key in [
        "analysis_output",
        "analysis_case_id",
        "analysis_pipeline",
        "analysis_started_at",
        "analysis_finished_at",
        "saved_output_path",
    ]:
        st.session_state[key] = None

    if RUNTIME_UPLOAD_DIR.exists():
        shutil.rmtree(RUNTIME_UPLOAD_DIR)

    st.rerun()


def configure_page() -> None:
    st.set_page_config(
        page_title="LegalMove Contract Intelligence",
        page_icon="⚖️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .main {
            background-color: #F4E9D8;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .legalmove-title {
            font-size: 2.3rem;
            font-weight: 800;
            color: #2B2118;
            margin-bottom: 0.2rem;
        }

        .legalmove-subtitle {
            font-size: 1rem;
            color: #1E1E1E;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 0.8rem;
            background-color: #FFF9EF;
            border: 1px solid #E8D8C3;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="legalmove-title">⚖️ LegalMove Contract Intelligence</div>
        <div class="legalmove-subtitle">
        Multimodal contract comparison with image parsing, structural contextualization,
        extraction agents, Langfuse tracing and LangSmith observability.
        </div>
        """,
        unsafe_allow_html=True,
    )


def save_uploaded_file(uploaded_file, case_id: str, target_name: str) -> Path:
    RUNTIME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    extension = Path(uploaded_file.name).suffix.lower()
    target_path = RUNTIME_UPLOAD_DIR / case_id / f"{target_name}{extension}"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("wb") as file:
        file.write(uploaded_file.getbuffer())

    return target_path


def run_selected_pipeline(
    pipeline: str,
    case_id: str,
    original_path: str,
    amendment_path: str,
    vision_provider: str,
    llm_provider: str,
) -> dict[str, Any]:
    if pipeline == "image-parsing":
        return run_image_parsing_graph(
            case_id=case_id,
            original_image_path=original_path,
            amendment_image_path=amendment_path,
            vision_provider=vision_provider,
        )

    if pipeline == "contextualization":
        return run_contextualization_graph(
            case_id=case_id,
            original_image_path=original_path,
            amendment_image_path=amendment_path,
            vision_provider=vision_provider,
            llm_provider=llm_provider,
        )

    return run_extraction_graph(
        case_id=case_id,
        original_image_path=original_path,
        amendment_image_path=amendment_path,
        vision_provider=vision_provider,
        llm_provider=llm_provider,
    )


def save_streamlit_output(case_id: str, pipeline: str, output: dict[str, Any]) -> Path:
    STREAMLIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = STREAMLIT_OUTPUT_DIR / f"{case_id}_{pipeline}_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    return output_path


def get_token_value(usage: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in usage and usage[key] is not None:
            return usage[key]

    return None


def normalize_usage_row(
    stage: str,
    provider: str | None,
    model: str | None,
    usage: dict[str, Any] | None,
    latency_seconds: float | None,
) -> dict[str, Any]:
    usage = usage or {}

    return {
        "stage": stage,
        "provider": provider or "N/A",
        "model": model or "N/A",
        "prompt_tokens": get_token_value(
            usage,
            "prompt_tokens",
            "input_tokens",
        ),
        "completion_tokens": get_token_value(
            usage,
            "completion_tokens",
            "output_tokens",
        ),
        "total_tokens": get_token_value(
            usage,
            "total_tokens",
        ),
        "latency_seconds": latency_seconds,
    }


def build_usage_table(output: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    original = output.get("original_contract", {})
    amendment = output.get("amendment", {})
    contextualization = output.get("contextualization", {})
    extraction = output.get("extraction", {})

    if original:
        rows.append(
            normalize_usage_row(
                stage="parse_original_contract",
                provider=original.get("provider"),
                model=original.get("model"),
                usage=original.get("usage"),
                latency_seconds=original.get("latency_seconds"),
            )
        )

    if amendment:
        rows.append(
            normalize_usage_row(
                stage="parse_amendment_contract",
                provider=amendment.get("provider"),
                model=amendment.get("model"),
                usage=amendment.get("usage"),
                latency_seconds=amendment.get("latency_seconds"),
            )
        )

    if contextualization:
        rows.append(
            normalize_usage_row(
                stage="contextualization_agent",
                provider=contextualization.get("llm_provider"),
                model=contextualization.get("llm_model"),
                usage=contextualization.get("usage"),
                latency_seconds=contextualization.get("latency_seconds"),
            )
        )

    if extraction:
        rows.append(
            normalize_usage_row(
                stage="extraction_agent",
                provider=extraction.get("llm_provider"),
                model=extraction.get("llm_model"),
                usage=extraction.get("usage"),
                latency_seconds=extraction.get("latency_seconds"),
            )
        )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return dataframe

    return dataframe[
        [
            "stage",
            "provider",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_seconds",
        ]
    ]


def build_changes_table(output: dict[str, Any]) -> pd.DataFrame:
    extraction = output.get("extraction", {})
    rows: list[dict[str, Any]] = []

    for collection_name in ["additions", "deletions", "modifications"]:
        for item in extraction.get(collection_name, []):
            rows.append(
                {
                    "change_type": item.get("change_type"),
                    "section_id": item.get("affected_section_id"),
                    "section_title": item.get("affected_section_title"),
                    "legal_topic": item.get("legal_topic"),
                    "impact_level": item.get("impact_level"),
                    "change_summary": item.get("change_summary"),
                    "original_text": item.get("original_text"),
                    "amendment_text": item.get("amendment_text"),
                }
            )

    return pd.DataFrame(rows)


def build_correspondence_table(output: dict[str, Any]) -> pd.DataFrame:
    contextualization = output.get("contextualization", {})
    rows = contextualization.get("section_correspondences", [])

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def build_observability_comparison_table() -> pd.DataFrame:
    status = get_observability_status()

    return pd.DataFrame(
        [
            {
                "tool": "Langfuse",
                "role": "Custom product observability",
                "best_for": "Pipeline traces, spans, generations, costs, tokens and session-level metadata.",
                "current_status": "enabled"
                if status.get("langfuse_enabled")
                else "disabled",
                "local_identifier": "contract-analysis / case_id",
            },
            {
                "tool": "LangSmith",
                "role": "LangChain and LangGraph native observability",
                "best_for": "Runnable traces, graph execution waterfall, LLM calls and LangChain metadata.",
                "current_status": "enabled"
                if status.get("langsmith_enabled")
                else "disabled",
                "local_identifier": status.get(
                    "langsmith_project",
                    "legalmove-contract-intelligence",
                ),
            },
        ]
    )


def render_sidebar() -> dict[str, Any]:
    st.sidebar.header("Analysis Controls")

    if st.sidebar.button("Reset analysis", use_container_width=True):
        reset_state()

    st.sidebar.divider()

    pipeline = st.sidebar.selectbox(
        "Pipeline",
        options=["extraction", "contextualization", "image-parsing"],
        index=0,
    )

    vision_provider = st.sidebar.selectbox(
        "Vision provider",
        options=["openai", "xai"],
        index=0,
    )

    llm_provider = st.sidebar.selectbox(
        "Text LLM provider",
        options=["openai", "xai", "deepseek"],
        index=0,
    )

    st.sidebar.divider()

    input_mode = st.sidebar.radio(
        "Input mode",
        options=["Sample case", "Upload files"],
        index=0,
    )

    selected_case_id = None
    original_path = None
    amendment_path = None
    original_upload = None
    amendment_upload = None

    if input_mode == "Sample case":
        selected_case_id = st.sidebar.selectbox(
            "Sample case",
            options=list(SAMPLE_CASES.keys()),
            format_func=lambda key: SAMPLE_CASES[key]["label"],
            index=0,
        )

        original_path = SAMPLE_CASES[selected_case_id]["original"]
        amendment_path = SAMPLE_CASES[selected_case_id]["amendment"]
        case_id = selected_case_id

    else:
        case_id = st.sidebar.text_input(
            "Case ID",
            value="uploaded_case",
        )

        original_upload = st.sidebar.file_uploader(
            "Original contract image",
            type=["png", "jpg", "jpeg"],
        )

        amendment_upload = st.sidebar.file_uploader(
            "Amendment image",
            type=["png", "jpg", "jpeg"],
        )

    run_button = st.sidebar.button(
        "Run analysis",
        type="primary",
        use_container_width=True,
    )

    return {
        "pipeline": pipeline,
        "vision_provider": vision_provider,
        "llm_provider": llm_provider,
        "input_mode": input_mode,
        "case_id": case_id,
        "original_path": original_path,
        "amendment_path": amendment_path,
        "original_upload": original_upload,
        "amendment_upload": amendment_upload,
        "run_button": run_button,
    }


def render_input_preview(
    input_mode: str,
    original_path: Path | None,
    amendment_path: Path | None,
    original_upload,
    amendment_upload,
) -> None:
    st.subheader("Input Documents")

    left, right = st.columns(2)

    with left:
        st.markdown("**Original Contract**")

        if input_mode == "Sample case" and original_path:
            st.image(str(original_path), use_container_width=True)
            st.caption(str(original_path))
        elif original_upload:
            st.image(original_upload, use_container_width=True)

    with right:
        st.markdown("**Amendment**")

        if input_mode == "Sample case" and amendment_path:
            st.image(str(amendment_path), use_container_width=True)
            st.caption(str(amendment_path))
        elif amendment_upload:
            st.image(amendment_upload, use_container_width=True)


def render_result_summary(output: dict[str, Any]) -> None:
    extraction = output.get("extraction", {})
    contextualization = output.get("contextualization", {})

    additions = len(extraction.get("additions", []))
    deletions = len(extraction.get("deletions", []))
    modifications = len(extraction.get("modifications", []))
    confidence = extraction.get(
        "confidence_score",
        contextualization.get("confidence_score", "N/A"),
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Additions", additions)
    col2.metric("Deletions", deletions)
    col3.metric("Modifications", modifications)
    col4.metric("Confidence", confidence)

    if extraction.get("summary_of_the_change"):
        st.info(extraction["summary_of_the_change"])
    elif contextualization.get("structural_summary"):
        st.info(contextualization["structural_summary"])


def render_structured_output(output: dict[str, Any]) -> None:
    tab_summary, tab_changes, tab_sections, tab_usage, tab_observability, tab_json = st.tabs(
        [
            "Summary",
            "Changes",
            "Section Map",
            "Tokens & Latency",
            "Tracing",
            "Raw JSON",
        ]
    )

    with tab_summary:
        render_result_summary(output)

        extraction = output.get("extraction", {})

        if extraction.get("topics_touched"):
            st.markdown("### Topics Touched")
            st.write(", ".join(extraction["topics_touched"]))

        if extraction.get("sections_changed"):
            st.markdown("### Sections Changed")
            st.write(", ".join(extraction["sections_changed"]))

    with tab_changes:
        st.markdown("### Detected Contract Changes")
        changes_df = build_changes_table(output)

        if changes_df.empty:
            st.warning("No final extraction changes found for this pipeline output.")
        else:
            st.dataframe(
                changes_df,
                use_container_width=True,
                hide_index=True,
            )

    with tab_sections:
        st.markdown("### Structural Section Correspondences")
        correspondence_df = build_correspondence_table(output)

        if correspondence_df.empty:
            st.warning("No contextual section correspondences found.")
        else:
            st.dataframe(
                correspondence_df,
                use_container_width=True,
                hide_index=True,
            )

    with tab_usage:
        st.markdown("### Token Usage and Latency")
        usage_df = build_usage_table(output)

        if usage_df.empty:
            st.warning("No usage metadata found.")
        else:
            st.dataframe(
                usage_df,
                use_container_width=True,
                hide_index=True,
            )

            numeric_total = pd.to_numeric(
                usage_df["total_tokens"],
                errors="coerce",
            ).sum()

            numeric_latency = pd.to_numeric(
                usage_df["latency_seconds"],
                errors="coerce",
            ).sum()

            col1, col2 = st.columns(2)
            col1.metric("Known Total Tokens", int(numeric_total))
            col2.metric("Total Latency Seconds", round(float(numeric_latency), 3))

    with tab_observability:
        st.markdown("### Langfuse vs LangSmith")

        st.dataframe(
            build_observability_comparison_table(),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Current Observability Status")
        status = get_observability_status()
        st.json(status)

        st.caption(
            "This view shows a lightweight local comparison. "
            "The full trace details remain available inside Langfuse and LangSmith."
        )

    with tab_json:
        st.markdown("### Raw JSON Output")
        st.json(output)

        json_bytes = json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")

        st.download_button(
            label="Download JSON",
            data=json_bytes,
            file_name=f"{output.get('case_id', 'analysis')}_output.json",
            mime="application/json",
        )


def main() -> None:
    configure_page()
    initialize_state()
    render_header()

    controls = render_sidebar()

    render_input_preview(
        input_mode=controls["input_mode"],
        original_path=controls["original_path"],
        amendment_path=controls["amendment_path"],
        original_upload=controls["original_upload"],
        amendment_upload=controls["amendment_upload"],
    )

    if controls["run_button"]:
        case_id = controls["case_id"]

        if not case_id:
            st.error("Case ID is required.")
            st.stop()

        if controls["input_mode"] == "Upload files":
            if not controls["original_upload"] or not controls["amendment_upload"]:
                st.error("Please upload both the original contract and amendment images.")
                st.stop()

            original_path = save_uploaded_file(
                uploaded_file=controls["original_upload"],
                case_id=case_id,
                target_name="original_contract",
            )

            amendment_path = save_uploaded_file(
                uploaded_file=controls["amendment_upload"],
                case_id=case_id,
                target_name="amendment",
            )
        else:
            original_path = controls["original_path"]
            amendment_path = controls["amendment_path"]

        started_at = datetime.now()

        with st.spinner("Running LegalMove contract analysis..."):
            output = run_selected_pipeline(
                pipeline=controls["pipeline"],
                case_id=case_id,
                original_path=str(original_path),
                amendment_path=str(amendment_path),
                vision_provider=controls["vision_provider"],
                llm_provider=controls["llm_provider"],
            )

        finished_at = datetime.now()
        saved_output_path = save_streamlit_output(
            case_id=case_id,
            pipeline=controls["pipeline"],
            output=output,
        )

        st.session_state.analysis_output = output
        st.session_state.analysis_case_id = case_id
        st.session_state.analysis_pipeline = controls["pipeline"]
        st.session_state.analysis_started_at = started_at
        st.session_state.analysis_finished_at = finished_at
        st.session_state.saved_output_path = saved_output_path

        st.success("Analysis completed successfully.")

    if st.session_state.analysis_output:
        st.divider()

        st.subheader("Analysis Result")

        col1, col2, col3 = st.columns(3)
        col1.metric("Case ID", st.session_state.analysis_case_id)
        col2.metric("Pipeline", st.session_state.analysis_pipeline)
        col3.metric(
            "Saved Output",
            str(st.session_state.saved_output_path.name)
            if st.session_state.saved_output_path
            else "N/A",
        )

        render_structured_output(st.session_state.analysis_output)


if __name__ == "__main__":
    main()