from typing import Any

from pydantic import BaseModel, Field


class ParsedContractText(BaseModel):
    source_path: str = Field(
        description="Path of the parsed contract image."
    )
    file_name: str = Field(
        description="Name of the parsed image file."
    )
    document_type: str = Field(
        description="Type of document parsed: original_contract or amendment."
    )
    provider: str = Field(
        description="Vision provider used for parsing."
    )
    model: str = Field(
        description="Vision model used for parsing."
    )
    mime_type: str = Field(
        description="Image MIME type."
    )
    extracted_text: str = Field(
        description="Full text extracted from the contract image."
    )
    character_count: int = Field(
        description="Number of extracted characters."
    )
    latency_seconds: float = Field(
        description="Parsing latency in seconds."
    )
    usage: dict[str, Any] = Field(
        default_factory=dict,
        description="Token usage metadata returned by the provider, when available."
    )


class ImageParsingPairOutput(BaseModel):
    case_id: str = Field(
        description="Identifier of the contract analysis case."
    )
    original_contract: ParsedContractText = Field(
        description="Parsed text and metadata for the original contract."
    )
    amendment: ParsedContractText = Field(
        description="Parsed text and metadata for the amendment document."
    )