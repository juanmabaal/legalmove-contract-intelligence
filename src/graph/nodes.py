from src.agents.contextualization_agent import run_contextualization_agent
from src.agents.extraction_agent import run_extraction_agent
from src.graph.state import ContractAnalysisState
from src.image_parser import parse_contract_image
from src.models import (
    ContractContextualizationPipelineOutput,
    ContractExtractionPipelineOutput,
    ImageParsingPairOutput,
)


def parse_original_contract_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    parsed_original = parse_contract_image(
        image_path=state["original_image_path"],
        document_type="original_contract",
        provider=state.get("vision_provider"),
    )

    return {
        **state,
        "original_contract": parsed_original,
    }


def parse_amendment_contract_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    parsed_amendment = parse_contract_image(
        image_path=state["amendment_image_path"],
        document_type="amendment",
        provider=state.get("vision_provider"),
    )

    return {
        **state,
        "amendment": parsed_amendment,
    }


def contextualization_agent_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    contextualization = run_contextualization_agent(
        case_id=state["case_id"],
        original_contract_text=state["original_contract"].extracted_text,
        amendment_text=state["amendment"].extracted_text,
        provider=state.get("llm_provider"),
    )

    return {
        **state,
        "contextualization": contextualization,
    }


def extraction_agent_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    extraction = run_extraction_agent(
        case_id=state["case_id"],
        original_contract_text=state["original_contract"].extracted_text,
        amendment_text=state["amendment"].extracted_text,
        contextualization=state["contextualization"],
        provider=state.get("llm_provider"),
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