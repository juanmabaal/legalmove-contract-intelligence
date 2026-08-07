import json
import re
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.observability.tracing import get_langfuse_callbacks, trace_generation

from src.config.settings import LLM_PROVIDER
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

def _get_model_name(llm: Any) -> str:
    return str(
        getattr(
            llm,
            "model_name",
            getattr(llm, "model", "unknown"),
        )
    )

def _extract_usage_metadata(response: Any) -> dict[str, Any]:
    usage_metadata = getattr(response, "usage_metada", None)

    if usage_metadata:
        return dict(usage_metadata)

    response_metadata = getattr(response, "response_metadata", {}) or {}

    if "token_usage" in response_metadata:
        return response_metadata["token_usage"]

    if "usage" in response_metadata:
        return response_metadata["usage"]

    return {}

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
    case_id: str,
    original_contract_text: str,
    amendment_text: str,
    provider: str | None = None,
) -> ContextualizationOutput:
    started_at = time.perf_counter()

    llm = get_chat_model(
        provider=provider,
        temperature=0,
    )

    selected_provider = provider or LLM_PROVIDER
    model_name = _get_model_name(llm)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZATION_SYSTEM_PROMPT),
            ("user", CONTEXTUALIZATION_USER_PROMPT),
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

    callbacks = get_langfuse_callbacks()

    llm_config: dict[str, Any] = {
        "run_name": "contextualization_llm",
        "tags": ["legalmove", "contextualization-agent"],
        "metadata": {
            "case_id": case_id,
            "agent": "ContextualizationAgent",
            "provider": selected_provider,
            "model": model_name,
        },
    }

    if callbacks:
        llm_config["callbacks"] = callbacks

    with trace_generation(
        name="contextualization_agent_generation",
        model=model_name,
        input_data={
            "case_id": case_id,
            "original_contract_length": len(original_contract_text),
            "amendment_length": len(amendment_text),
        },
        metadata={
            "agent": "ContextualizationAgent",
            "provider": selected_provider,
            "model": model_name,
        },
    ) as generation:
        response = llm.invoke(
            messages,
            config=llm_config,
        )

        response_text = _extract_response_text(response)
        usage = _extract_usage_metadata(response)

        generation.update(
            output_data={
                "response_preview": response_text[:2000],
            },
            metadata={
                "usage": usage,
            },
        )

    response_data = _extract_json_object(response_text)

    response_data["case_id"] = response_data.get("case_id", case_id)
    response_data["llm_provider"] = selected_provider
    response_data["llm_model"] = model_name
    response_data["usage"] = usage

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
            "llm_provider": selected_provider,
            "llm_model": model_name,
            "usage": usage,
        }
    )

    return contextualization_output