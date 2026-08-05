from typing import Any, Literal

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

class ContractSection(BaseModel):
    section_id: str = Field(
        description="Section identifier as it appears or can be inferred from the document."
    )
    title: str = Field(
        description="Section tottle or shot descriptive name"
    )
    source_document: Literal["original_contract", "amendment"] = Field(
        description="Document where this section was found."
    )
    text_excerpt: str = Field(
        description="Short excerpt that represents the section content."
    )
    purpose: str = Field(
        description="Functional purpose of the section within the legal document."
    )

class SectionCorrespondence(BaseModel):
    original_section_id: str | None = Field(
        default=None,
        description="Matching section identifier from the original contract, if any."
    )
    amendment_section_id: str | None = Field(
        default=None,
        description="Matching section identifier from the amendment, if any."
    )
    relationship_type: Literal[
        "same_or_equivalent",
        "appears_structurally_modified",
        "new_in_amendment",
        "missing_from_amendment",
        "unclear",
    ] = Field(
        description="Structural relationship between original and amendment sections."
    )
    rationale: str = Field(
        description="Reason why these sections are considered related or structurally different."
    )

class ContextualizationOutput(BaseModel):
    case_id: str = Field(
        description="Identifier of the contract analysis case."
    )
    original_sections: list[ContractSection] = Field(
        description="Sections identified in the original contract."
    )
    amendment_sections: list[ContractSection] = Field(
        description="Sections identified in the amendment document."
    )
    section_correspondences: list[SectionCorrespondence] = Field(
        description="Structural correspondences between original and amendment sections."
    )
    new_blocks_in_amendment: list[str] = Field(
        description="Blocks or sections that appear structurally new in the amendment."
    )
    potentially_missing_blocks: list[str] = Field(
        description="Sections from the original that appear missing or not clearly represented in the amendment."
    )
    structural_summary: str = Field(
        description="High-level structural summary of how the amendment relates to the original contract."
    )
    confidence_score: float = Field(
        ge=0,
        le=1,
        description="Confidence score for the structural map, from 0 to 1."
    )
    latency_seconds: float = Field(
        default=0.0,
        description="Contextualization agent latency in seconds."
    )

class ContractContextualizationPipelineOutput(BaseModel):
    case_id: str = Field(
        description="Identifier of the contract analysis case."
    )
    original_contract: ParsedContractText = Field(
        description="Parsed original contract text and metadata."
    )
    amendment: ParsedContractText = Field(
        description="Parsed amendment text and metadata."
    )
    contextualization: ContextualizationOutput = Field(
        description="Structural comparative map produced by the ContextualizationAgent."
    )
