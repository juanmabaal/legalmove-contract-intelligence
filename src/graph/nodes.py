from src.agents.contextualization_agent import run_contextualization_agent
from src.agents.extraction_agent import run_extraction_agent
from src.graph.state import ContractAnalysisState
from src.image_parser import parse_contract_image
from src.observability.tracing import trace_step
from src.models import (
    ContractContextualizationPipelineOutput,
    ContractExtractionPipelineOutput,
    ImageParsingPairOutput,
)


def parse_original_contract_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    with trace_step(
        name="parse_original_contract",
        input_data={
            "case_id": state["case_id"],
            "image_path": state["original_image_path"],
            "vision_provider": state.get("vision_provider"),
        },
        metadata={
            "node": "parse_original_contract",
            "document_type": "original_contract",
        },
    ) as span:
        parsed_original = parse_contract_image(
            image_path=state["original_image_path"],
            document_type="original_contract",
            provider=state.get("vision_provider"),
        )

        span.update(
            output_data={
                "file_name": parsed_original.file_name,
                "character_count": parsed_original.character_count,
                "latency_seconds": parsed_original.latency_seconds,
                "usage": parsed_original.usage,
            }
        )

        return {
            **state,
            "original_contract": parsed_original,
        }


def parse_amendment_contract_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    with trace_step(
        name="parse_amendment_contract",
        input_data={
            "case_id": state["case_id"],
            "image_path": state["amendment_image_path"],
            "vision_provider": state.get("vision_provider"),
        },
        metadata={
            "node": "parse_amendment_contract",
            "document_type": "amendment",
        },
    ) as span:
        parsed_amendment = parse_contract_image(
            image_path=state["amendment_image_path"],
            document_type="amendment",
            provider=state.get("vision_provider"),
        )

        span.update(
            output_data={
                "file_name": parsed_amendment.file_name,
                "character_count": parsed_amendment.character_count,
                "latency_seconds": parsed_amendment.latency_seconds,
                "usage": parsed_amendment.usage,
            }
        )

        return {
            **state,
            "amendment": parsed_amendment,
        }


def contextualization_agent_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    with trace_step(
        name="contextualization_agent",
        input_data={
            "case_id": state["case_id"],
            "original_character_count": state["original_contract"].character_count,
            "amendment_character_count": state["amendment"].character_count,
            "llm_provider": state.get("llm_provider"),
        },
        metadata={
            "node": "contextualization_agent",
            "agent": "ContextualizationAgent",
        },
    ) as span:
        contextualization = run_contextualization_agent(
            case_id=state["case_id"],
            original_contract_text=state["original_contract"].extracted_text,
            amendment_text=state["amendment"].extracted_text,
            provider=state.get("llm_provider"),
        )

        span.update(
            output_data={
                "original_sections": len(contextualization.original_sections),
                "amendment_sections": len(contextualization.amendment_sections),
                "section_correspondences": len(
                    contextualization.section_correspondences
                ),
                "new_blocks_in_amendment": contextualization.new_blocks_in_amendment,
                "confidence_score": contextualization.confidence_score,
                "latency_seconds": contextualization.latency_seconds,
            }
        )

        return {
            **state,
            "contextualization": contextualization,
        }


def extraction_agent_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    with trace_step(
        name="extraction_agent",
        input_data={
            "case_id": state["case_id"],
            "llm_provider": state.get("llm_provider"),
            "contextualization_confidence": (
                state["contextualization"].confidence_score
            ),
        },
        metadata={
            "node": "extraction_agent",
            "agent": "ExtractionAgent",
        },
    ) as span:
        extraction = run_extraction_agent(
            case_id=state["case_id"],
            original_contract_text=state["original_contract"].extracted_text,
            amendment_text=state["amendment"].extracted_text,
            contextualization=state["contextualization"],
            provider=state.get("llm_provider"),
        )

        span.update(
            output_data={
                "sections_changed": extraction.sections_changed,
                "topics_touched": extraction.topics_touched,
                "additions_count": len(extraction.additions),
                "deletions_count": len(extraction.deletions),
                "modifications_count": len(extraction.modifications),
                "confidence_score": extraction.confidence_score,
                "latency_seconds": extraction.latency_seconds,
            }
        )

        return {
            **state,
            "extraction": extraction,
        }


def build_image_parsing_output_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    output = ImageParsingPairOutput(
        case_id=state["case_id"],
        original_contract=state["original_contract"],
        amendment=state["amendment"],
    )

    return {
        **state,
        "final_output": output.model_dump(),
        "error": None,
    }


def build_contextualization_output_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    output = ContractContextualizationPipelineOutput(
        case_id=state["case_id"],
        original_contract=state["original_contract"],
        amendment=state["amendment"],
        contextualization=state["contextualization"],
    )

    return {
        **state,
        "final_output": output.model_dump(),
        "error": None,
    }


def build_extraction_output_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    output = ContractExtractionPipelineOutput(
        case_id=state["case_id"],
        original_contract=state["original_contract"],
        amendment=state["amendment"],
        contextualization=state["contextualization"],
        extraction=state["extraction"],
    )

    return {
        **state,
        "final_output": output.model_dump(),
        "error": None,
    }