import base64
import time
from pathlib import Path

from src.models import ParsedContractText
from src.providers.vision_factory import get_vision_provider


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class ImageParserError(RuntimeError):
    """Raised when a contract image cannot be validated, encoded or parsed."""


def validate_image_path(image_path: str | Path) -> Path:
    path = Path(image_path)

    if not path.exists():
        raise ImageParserError(f"Image file does not exist: {path}")

    if not path.is_file():
        raise ImageParserError(f"Path is not a file: {path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        supported_extensions = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ImageParserError(
            f"Unsupported image extension: {suffix}. "
            f"Supported extensions: {supported_extensions}"
        )

    return path


def get_image_mime_type(image_path: str | Path) -> str:
    path = validate_image_path(image_path)
    suffix = path.suffix.lower()

    return SUPPORTED_IMAGE_EXTENSIONS[suffix]


def encode_image_to_base64(image_path: str | Path) -> str:
    path = validate_image_path(image_path)

    with path.open("rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    return encoded_image


def build_image_data_url(image_path: str | Path) -> str:
    path = validate_image_path(image_path)
    mime_type = get_image_mime_type(path)
    base64_image = encode_image_to_base64(path)

    return f"data:{mime_type};base64,{base64_image}"


def parse_contract_image(
    image_path: str | Path,
    document_type: str,
    provider: str | None = None,
) -> ParsedContractText:
    path = validate_image_path(image_path)
    mime_type = get_image_mime_type(path)
    image_data_url = build_image_data_url(path)

    vision_provider = get_vision_provider(provider)

    started_at = time.perf_counter()

    extracted_text, usage = vision_provider.parse_image(
        image_data_url=image_data_url,
        document_type=document_type,
    )

    latency_seconds = round(time.perf_counter() - started_at, 3)

    if not extracted_text.strip():
        raise ImageParserError(
            f"No text was extracted from image: {path}"
        )

    return ParsedContractText(
        source_path=str(path),
        file_name=path.name,
        document_type=document_type,
        provider=vision_provider.provider_name,
        model=vision_provider.model_name,
        mime_type=mime_type,
        extracted_text=extracted_text,
        character_count=len(extracted_text),
        latency_seconds=latency_seconds,
        usage=usage,
    )