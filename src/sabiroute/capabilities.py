"""Central typed capability and request-classification representations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal


class Capability(StrEnum):
    CHAT = "chat"
    INLINE_COMPLETION = "inline_completion"
    CODING = "coding"
    REASONING = "reasoning"
    VISION = "vision"
    LONG_CONTEXT = "long_context"
    TOOL_USE = "tool_use"
    STRUCTURED_OUTPUT = "structured_output"
    JSON = "json"
    STREAMING = "streaming"
    LOW_LATENCY = "low_latency"
    EMBEDDING = "embedding"
    MULTIMODAL = "multimodal"


CapabilityDeclaration = bool | Literal["unknown"]


class RequestType(StrEnum):
    INLINE_COMPLETION = "inline_completion"
    CHAT = "chat"
    CODING_AGENT = "coding_agent"


@dataclass(frozen=True, slots=True)
class DeploymentCapabilities:
    """Capabilities explicitly supported, unsupported, or left unknown."""

    supported: frozenset[Capability] = frozenset()
    unsupported: frozenset[Capability] = frozenset()

    def __post_init__(self) -> None:
        overlap = self.supported & self.unsupported
        if overlap:
            names = ", ".join(sorted(capability.value for capability in overlap))
            raise ValueError(f"Capabilities cannot be both supported and unsupported: {names}")

    def missing_requirements(
        self, required: Iterable[Capability]
    ) -> tuple[frozenset[Capability], frozenset[Capability]]:
        required_set = frozenset(required)
        unsupported = required_set & self.unsupported
        unknown = required_set - self.supported - self.unsupported
        return unsupported, unknown

    def supports(self, required: Iterable[Capability]) -> bool:
        unsupported, unknown = self.missing_requirements(required)
        return not unsupported and not unknown


@dataclass(frozen=True, slots=True)
class RequestClassification:
    """Deterministic, explainable facts derived from a completion request."""

    request_type: RequestType
    required_capabilities: frozenset[Capability]
    streaming_required: bool
    tool_use_required: bool
    structured_output_required: bool
    multimodal_required: bool
    vision_required: bool


_REQUEST_TYPE_CAPABILITY = {
    RequestType.INLINE_COMPLETION: Capability.INLINE_COMPLETION,
    RequestType.CHAT: Capability.CHAT,
    RequestType.CODING_AGENT: Capability.CODING,
}


def classify_request(
    *,
    explicit_type: RequestType | None,
    options: dict[str, Any],
    messages: list[dict[str, Any]],
    policy_requirements: Iterable[Capability] = (),
) -> RequestClassification:
    """Classify by API shape and caller-declared request type, without heuristics."""
    request_type = explicit_type or RequestType.CHAT
    # Preserve legacy ordinary-chat routing until deployments are explicitly
    # annotated. Explicit classes, policy requirements, and request features
    # still require verified capabilities.
    required: set[Capability] = set()
    if explicit_type is not None:
        required.add(Capability.CHAT)
        required.add(_REQUEST_TYPE_CAPABILITY[request_type])
    required.update(policy_requirements)

    streaming_required = options.get("stream") is True
    if streaming_required:
        required.add(Capability.STREAMING)

    tools = options.get("tools")
    tool_use_required = isinstance(tools, list) and bool(tools)
    tool_choice = options.get("tool_choice")
    if tool_choice is not None and tool_choice != "none":
        tool_use_required = True
    if tool_use_required:
        required.add(Capability.TOOL_USE)

    response_format = options.get("response_format")
    structured_output_required = response_format is not None
    if structured_output_required:
        required.add(Capability.STRUCTURED_OUTPUT)
        if isinstance(response_format, dict) and response_format.get("type") in {
            "json_object",
            "json_schema",
        }:
            required.add(Capability.JSON)

    multimodal_required = False
    vision_required = False
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            continue
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = part.get("type")
                if part_type in {"image", "image_url", "input_image"}:
                    multimodal_required = True
                    vision_required = True
                elif part_type in {
                    "input_audio",
                    "audio",
                    "video",
                    "input_video",
                }:
                    multimodal_required = True
    if multimodal_required:
        required.add(Capability.MULTIMODAL)
    if vision_required:
        required.add(Capability.VISION)

    return RequestClassification(
        request_type=request_type,
        required_capabilities=frozenset(required),
        streaming_required=streaming_required,
        tool_use_required=tool_use_required,
        structured_output_required=structured_output_required,
        multimodal_required=multimodal_required,
        vision_required=vision_required,
    )
