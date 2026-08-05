from typing import Any, TypedDict
from src.models import ContextualizationOutput, ParsedContractText

class ContractAnalysisState(TypedDict, total=False):
    case_id: str

    original_image_path: str
    amendment_image_path: str

    vision_provider: str
    llm_provider: str

    original_contract: ParsedContractText
    amendment: ParsedContractText

    contextualization: ContextualizationOutput

    final_output: dict[str,Any]

    error: str | None

