from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI
from src.observability.tracing import trace_generation

from src.config.settings import (
    OPENAI_API_KEY,
    OPENAI_VISION_MODEL,
    VISION_PROVIDER,
    XAI_API_KEY,
    XAI_BASE_URL,
    XAI_VISION_MODEL,
    validate_vision_provider,
)


VISION_EXTRACTION_PROMPT = """
You are a legal document OCR and structure extraction specialist.

Your task is to read the provided scanned contract image and extract the text as faithfully as possible.

Instructions:
- Extract all visible text.
- Preserve headings, section numbers, clause numbers and bullet structure.
- Preserve legal terminology exactly as written.
- Do not summarize.
- Do not add information that is not visible.
- If a section is unclear, write [UNCLEAR TEXT] only for that fragment.
- Keep the output in a clean markdown-like structure.
- Return only the extracted document text.
"""


class VisionProviderError(RuntimeError):
    """Raised when a vision provider cannot parse a document image."""


class BaseVisionProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def parse_image(
        self,
        image_data_url: str,
        document_type: str,
    ) -> tuple[str, dict[str, Any]]:
        """Parse an image data URL and return extracted text and usage metadata."""


class OpenAIVisionProvider(BaseVisionProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise VisionProviderError(
                "OPENAI_API_KEY is required when VISION_PROVIDER=openai."
            )

        self.model_name = OPENAI_VISION_MODEL
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def parse_image(
        self,
        image_data_url: str,
        document_type: str,
    ) -> tuple[str, dict[str, Any]]:
        try:
            with trace_generation(
                name="openai_vision_parse",
                model=self.model_name,
                input_data={
                    "document_type": document_type,
                    "image_input": "[base64_image_omitted]",
                    "provider": self.provider_name,
                },
                metadata={
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "document_type": document_type,
                },
            ) as generation:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": VISION_EXTRACTION_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Extract the full text from this "
                                        f"{document_type.replace('_', ' ')} image."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data_url,
                                        "detail": "high",
                                    },
                                },
                            ],
                        },
                    ],
                    temperature=0,
                )

                usage = {}

                if getattr(response, "usage", None):
                    usage = response.usage.model_dump()

                content = response.choices[0].message.content or ""
                extracted_text = content.strip()

                generation.update(
                    output_data={
                        "extracted_text": extracted_text,
                        "character_count": len(extracted_text),
                    },
                    metadata={
                        "usage": usage,
                    },
                )

                return extracted_text, usage

        except Exception as error:
            raise VisionProviderError(
                f"OpenAI vision parsing failed: {error}"
            ) from error

class XAIVisionProvider(BaseVisionProvider):
    provider_name = "xai"

    def __init__(self) -> None:
        if not XAI_API_KEY:
            raise VisionProviderError(
                "XAI_API_KEY is required when VISION_PROVIDER=xai."
            )

        self.model_name = XAI_VISION_MODEL
        self.client = OpenAI(
            api_key=XAI_API_KEY,
            base_url=XAI_BASE_URL,
        )

    def parse_image(
        self,
        image_data_url: str,
        document_type: str,
    ) -> tuple[str, dict[str, Any]]:
        try:
            with trace_generation(
                name="xai_vision_parse",
                model=self.model_name,
                input_data={
                    "document_type": document_type,
                    "image_input": "[base64_image_omitted]",
                    "provider": self.provider_name,
                },
                metadata={
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "document_type": document_type,
                },
            ) as generation:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": VISION_EXTRACTION_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Extract the full text from this "
                                        f"{document_type.replace('_', ' ')} image."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data_url,
                                    },
                                },
                            ],
                        },
                    ],
                    temperature=0,
                )

                usage: dict[str, Any] = {}

                if getattr(response, "usage", None):
                    usage = response.usage.model_dump()

                content = response.choices[0].message.content or ""
                extracted_text = content.strip()

                generation.update(
                    output_data={
                        "extracted_text": extracted_text,
                        "character_count": len(extracted_text),
                    },
                    metadata={
                        "usage": usage,
                    },
                )

                return extracted_text, usage

        except Exception as error:
            raise VisionProviderError(
                f"xAI vision parsing failed: {error}"
            ) from error


def get_vision_provider(provider: str | None = None) -> BaseVisionProvider:
    selected_provider = validate_vision_provider(provider or VISION_PROVIDER)

    if selected_provider == "openai":
        return OpenAIVisionProvider()

    if selected_provider == "xai":
        return XAIVisionProvider()

    raise VisionProviderError(
        f"Unsupported vision provider: {selected_provider}"
    )