import json
import re
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.models import ContextualizationOutput
from src.providers.llm_factory import get_chat_model


CONTEXTUALIZATION_SYSTEM_PROMPT = """
You are ContextualizationAgent, a specialized legal document structure analyst.

Your role is to compare the parsed text of an original contract and an amendment document.

Your task is NOT to extract final legal changes yet.
Your task is to create a structural comparative map that helps a downstream ExtractionAgent understand the documents.

You must identify:
- Sections in the original contract.
- Sections in the amendment.
- Sections that appear to correspond to each other.
- Sections that appear structurally new in the amendment.
- Sections from the original that appear missing or not clearly represented.
- The functional purpose of each section.

Strict rules:
- Do not provide legal advice.
- Do not produce a final change list.
- Do not classify additions, deletions or modifications as final legal changes.
- You may describe structural relationships only.
- Preserve legal terminology from the documents.
- Base your answer only on the provided texts.
- Return valid JSON only.
- Do not wrap the JSON in markdown.
"""

CONTEXTUALIZATION_USER_PROMPT = """
Case ID:
{case_id}

Expected JSON schema:
{json_schema}

Original contract parsed text:
{original_contract_text}

Amendment parsed text:
{amendment_text}

Return only valid JSON that matches the schema.
"""

class ContextualizationAgentError(RuntimeError):
    """Raised when the contextualization agent fails."""

def _extract_response_text(response:Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))

        return "\n".join(parts)

    return str(content)

def _extract_json_object(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ContextualizationAgentError(
            "The model response did not contain a valid JSON object."
        )

    json_text = cleaned[start : end + 1]

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ContextualizationAgentError(
             f"Failed to parse contextualization JSON: {error}"
        ) from error

def run_contextualization_agent(
        case_id : str,
        original_contract_text: str,
        amendment_text: str,
        provider: str | None = None,
) -> ContextualizationOutput:
    started_at = time.perf_counter()

    llm = get_chat_model(
        provider=provider,
        temperature=0
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZATION_SYSTEM_PROMPT),
            ("user", CONTEXTUALIZATION_USER_PROMPT)
        ]
    )

    json_schema = json.dumps(
        ContextualizationOutput.model_json_schema(),
        indent=2,
        ensure_ascii=False,
    )

    messages = prompt.format_messages(
        case_id=case_id,
        json_schema=json_schema,
        original_contract_text=original_contract_text,
        amendment_text=amendment_text,
    )

    response = llm.invoke(messages)
    response_text = _extract_response_text(response)
    response_data = _extract_json_object(response_text)

    try:
        contextualization_output = ContextualizationOutput.model_validate(
            response_data
        )
    except Exception as error:
        raise ContextualizationAgentError(
             f"Contextualization output validation failed: {error}"
        ) from error

    latency_seconds = round(time.perf_counter() - started_at, 3)

    contextualization_output = contextualization_output.model_copy(
        update={
            "latency_seconds": latency_seconds,
        }
    )

    return contextualization_output

