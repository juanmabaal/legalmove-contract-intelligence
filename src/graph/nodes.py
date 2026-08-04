from src.graph.state import ContractAnalysisState
from src.image_parser import parse_contract_image
from src.models import ImageParsingPairOutput

def parse_original_contract_node(
    state: ContractAnalysisState,
) -> ContractAnalysisState:
    parsed_original = parse_contract_image(
        image_path=state["original_image_path"],
        document_type="original_contract",
        provider=state.get("vision_provider")
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
        provider=state.get("vision_provider")
    )

    return {
        **state,
        "amendment": parsed_amendment,
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