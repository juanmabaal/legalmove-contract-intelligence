import os
from contextlib import contextmanager, nullcontext
from typing import Any, Iterator

from src.config.settings import (
    APP_ENV,
    LANGCHAIN_API_KEY,
    LANGCHAIN_CALLBACKS_BACKGROUND,
    LANGCHAIN_ENDPOINT,
    LANGCHAIN_PROJECT,
    LANGCHAIN_TRACING_V2,
    LANGFUSE_BASE_URL,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)


def _is_truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def configure_langfuse_environment() -> None:
    if LANGFUSE_PUBLIC_KEY:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", LANGFUSE_PUBLIC_KEY)

    if LANGFUSE_SECRET_KEY:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", LANGFUSE_SECRET_KEY)

    if LANGFUSE_HOST:
        os.environ.setdefault("LANGFUSE_HOST", LANGFUSE_HOST)

    if LANGFUSE_BASE_URL:
        os.environ.setdefault("LANGFUSE_BASE_URL", LANGFUSE_BASE_URL)


def configure_langsmith_environment() -> None:
    if LANGSMITH_API_KEY:
        os.environ.setdefault("LANGSMITH_API_KEY", LANGSMITH_API_KEY)

    if LANGSMITH_PROJECT:
        os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)

    os.environ.setdefault("LANGSMITH_TRACING", LANGSMITH_TRACING)

    if LANGCHAIN_API_KEY:
        os.environ.setdefault("LANGCHAIN_API_KEY", LANGCHAIN_API_KEY)

    if LANGCHAIN_PROJECT:
        os.environ.setdefault("LANGCHAIN_PROJECT", LANGCHAIN_PROJECT)

    if LANGCHAIN_ENDPOINT:
        os.environ.setdefault("LANGCHAIN_ENDPOINT", LANGCHAIN_ENDPOINT)

    os.environ.setdefault("LANGCHAIN_TRACING_V2", LANGCHAIN_TRACING_V2)
    os.environ.setdefault(
        "LANGCHAIN_CALLBACKS_BACKGROUND",
        LANGCHAIN_CALLBACKS_BACKGROUND,
    )


def configure_observability_environment() -> None:
    configure_langfuse_environment()
    configure_langsmith_environment()


def is_langfuse_enabled() -> bool:
    return bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)


def is_langsmith_enabled() -> bool:
    has_api_key = bool(LANGSMITH_API_KEY or LANGCHAIN_API_KEY)
    tracing_enabled = _is_truthy(LANGSMITH_TRACING) or _is_truthy(
        LANGCHAIN_TRACING_V2
    )

    return has_api_key and tracing_enabled


def get_observability_status() -> dict[str, Any]:
    return {
        "langfuse_enabled": is_langfuse_enabled(),
        "langsmith_enabled": is_langsmith_enabled(),
        "langsmith_project": LANGSMITH_PROJECT or LANGCHAIN_PROJECT,
        "environment": APP_ENV,
    }


class ObservationHandle:
    def __init__(self, observation: Any | None = None) -> None:
        self.observation = observation

    def update(
        self,
        input_data: Any | None = None,
        output_data: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self.observation is None:
            return

        payload: dict[str, Any] = {}

        if input_data is not None:
            payload["input"] = input_data

        if output_data is not None:
            payload["output"] = output_data

        if metadata is not None:
            payload["metadata"] = metadata

        if not payload:
            return

        try:
            self.observation.update(**payload)
        except Exception:
            # Observability must never break the business pipeline.
            return


def _get_langfuse_client() -> Any | None:
    if not is_langfuse_enabled():
        return None

    try:
        configure_langfuse_environment()

        from langfuse import get_client

        return get_client()
    except Exception:
        return None


def _get_propagation_context(
    case_id: str,
    pipeline: str,
    tags: list[str],
    metadata: dict[str, Any],
):
    try:
        from langfuse import propagate_attributes

        return propagate_attributes(
            session_id=case_id,
            tags=tags,
            metadata={
                **metadata,
                "case_id": case_id,
                "pipeline": pipeline,
                "environment": APP_ENV,
            },
        )
    except Exception:
        return nullcontext()


def _start_langfuse_observation(
    name: str,
    as_type: str,
    input_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
    model: str | None = None,
):
    client = _get_langfuse_client()

    if client is None:
        return nullcontext(None)

    try:
        if hasattr(client, "start_as_current_observation"):
            kwargs: dict[str, Any] = {
                "as_type": as_type,
                "name": name,
            }

            if input_data is not None:
                kwargs["input"] = input_data

            if metadata is not None:
                kwargs["metadata"] = metadata

            if model is not None:
                kwargs["model"] = model

            return client.start_as_current_observation(**kwargs)

        if hasattr(client, "start_as_current_span"):
            kwargs = {
                "name": name,
            }

            if input_data is not None:
                kwargs["input"] = input_data

            if metadata is not None:
                kwargs["metadata"] = metadata

            return client.start_as_current_span(**kwargs)

    except Exception:
        return nullcontext(None)

    return nullcontext(None)


@contextmanager
def trace_pipeline_run(
    pipeline: str,
    case_id: str,
    input_data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> Iterator[ObservationHandle]:
    configure_observability_environment()

    trace_metadata = {
        "case_id": case_id,
        "pipeline": pipeline,
        "environment": APP_ENV,
        **(metadata or {}),
    }

    tags = [
        "legalmove",
        "contract-intelligence",
        pipeline,
        APP_ENV,
    ]

    with _start_langfuse_observation(
        name="contract-analysis",
        as_type="span",
        input_data=input_data,
        metadata=trace_metadata,
    ) as observation:
        handle = ObservationHandle(observation)

        with _get_propagation_context(
            case_id=case_id,
            pipeline=pipeline,
            tags=tags,
            metadata=trace_metadata,
        ):
            try:
                yield handle
            except Exception as error:
                handle.update(
                    output_data={"error": str(error)},
                    metadata={
                        **trace_metadata,
                        "status": "error",
                    },
                )
                raise


@contextmanager
def trace_step(
    name: str,
    input_data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[ObservationHandle]:
    with _start_langfuse_observation(
        name=name,
        as_type="span",
        input_data=input_data,
        metadata=metadata,
    ) as observation:
        handle = ObservationHandle(observation)

        try:
            yield handle
        except Exception as error:
            handle.update(
                output_data={"error": str(error)},
                metadata={
                    **(metadata or {}),
                    "status": "error",
                },
            )
            raise


@contextmanager
def trace_generation(
    name: str,
    model: str,
    input_data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[ObservationHandle]:
    with _start_langfuse_observation(
        name=name,
        as_type="generation",
        input_data=input_data,
        metadata=metadata,
        model=model,
    ) as observation:
        handle = ObservationHandle(observation)

        try:
            yield handle
        except Exception as error:
            handle.update(
                output_data={"error": str(error)},
                metadata={
                    **(metadata or {}),
                    "status": "error",
                },
            )
            raise


def get_langfuse_callbacks() -> list[Any]:
    if not is_langfuse_enabled():
        return []

    try:
        configure_langfuse_environment()

        from langfuse.langchain import CallbackHandler

        return [CallbackHandler()]
    except Exception:
        return []


def build_langsmith_config(
    run_name: str,
    case_id: str,
    pipeline: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    configure_langsmith_environment()

    base_metadata = {
        "case_id": case_id,
        "pipeline": pipeline,
        "environment": APP_ENV,
        **(metadata or {}),
    }

    config: dict[str, Any] = {
        "run_name": run_name,
        "tags": [
            "legalmove",
            "contract-intelligence",
            pipeline,
            APP_ENV,
        ],
        "metadata": base_metadata,
    }

    return config


def flush_observability() -> None:
    client = _get_langfuse_client()

    if client is not None:
        try:
            client.flush()
        except Exception:
            pass