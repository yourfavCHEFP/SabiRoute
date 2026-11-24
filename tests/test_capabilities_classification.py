"""Behavioural tests for :mod:`sabiroute.capabilities`."""
from __future__ import annotations

from typing import Any

import pytest

from sabiroute.capabilities import (
    Capability,
    DeploymentCapabilities,
    RequestType,
    classify_request,
)


def _classify(**overrides: Any) -> Any:
    params: dict[str, Any] = {
        "explicit_type": None,
        "options": {},
        "messages": [{"role": "user", "content": "hi"}],
    }
    params.update(overrides)
    return classify_request(**params)


def test_deployment_capabilities_reject_supported_unsupported_overlap() -> None:
    with pytest.raises(ValueError) as excinfo:
        DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.CHAT}),
        )

    assert "cannot be both supported and unsupported" in str(excinfo.value)


def test_missing_requirements_splits_unsupported_from_unknown() -> None:
    declared = DeploymentCapabilities(
        supported=frozenset({Capability.CHAT}),
        unsupported=frozenset({Capability.VISION}),
    )

    unsupported, unknown = declared.missing_requirements(
        [Capability.CHAT, Capability.VISION, Capability.TOOL_USE]
    )

    assert unsupported == frozenset({Capability.VISION})
    assert unknown == frozenset({Capability.TOOL_USE})


def test_supports_requires_every_capability_to_be_verified() -> None:
    declared = DeploymentCapabilities(supported=frozenset({Capability.CHAT}))

    assert declared.supports([Capability.CHAT]) is True
    assert declared.supports([Capability.CHAT, Capability.LONG_CONTEXT]) is False


def test_plain_chat_requires_no_capabilities_by_default() -> None:
    classification = _classify()

    assert classification.request_type is RequestType.CHAT
    assert classification.required_capabilities == frozenset()
    assert classification.streaming_required is False


def test_explicit_request_type_requires_chat_plus_the_declared_capability() -> None:
    classification = _classify(explicit_type=RequestType.CODING_AGENT)

    assert classification.request_type is RequestType.CODING_AGENT
    assert classification.required_capabilities == frozenset(
        {Capability.CHAT, Capability.CODING}
    )


def test_policy_requirements_are_added_to_the_required_set() -> None:
    classification = _classify(policy_requirements=[Capability.LONG_CONTEXT])

    assert Capability.LONG_CONTEXT in classification.required_capabilities


def test_streaming_flag_adds_the_streaming_capability() -> None:
    assert Capability.STREAMING in _classify(options={"stream": True}).required_capabilities
    assert Capability.STREAMING not in _classify(options={"stream": False}).required_capabilities


def test_tools_or_tool_choice_require_tool_use() -> None:
    assert Capability.TOOL_USE in _classify(
        options={"tools": [{"type": "function"}]}
    ).required_capabilities
    assert Capability.TOOL_USE not in _classify(options={"tools": []}).required_capabilities
    assert Capability.TOOL_USE in _classify(
        options={"tool_choice": "auto"}
    ).required_capabilities
    assert Capability.TOOL_USE not in _classify(
        options={"tool_choice": "none"}
    ).required_capabilities


def test_json_response_format_requires_structured_output_and_json() -> None:
    classification = _classify(options={"response_format": {"type": "json_schema"}})

    assert classification.structured_output_required is True
    assert {
        Capability.STRUCTURED_OUTPUT,
        Capability.JSON,
    } <= classification.required_capabilities


def test_plain_response_format_requires_only_structured_output() -> None:
    classification = _classify(options={"response_format": {"type": "text"}})

    assert Capability.STRUCTURED_OUTPUT in classification.required_capabilities
    assert Capability.JSON not in classification.required_capabilities


def test_image_parts_require_multimodal_and_vision() -> None:
    messages = [
        {
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": "x"}}],
        }
    ]

    classification = _classify(messages=messages)

    assert classification.multimodal_required is True
    assert classification.vision_required is True
    assert {Capability.MULTIMODAL, Capability.VISION} <= classification.required_capabilities


def test_audio_parts_require_multimodal_without_vision() -> None:
    messages = [{"role": "user", "content": [{"type": "input_audio"}]}]

    classification = _classify(messages=messages)

    assert classification.multimodal_required is True
    assert classification.vision_required is False
    assert Capability.MULTIMODAL in classification.required_capabilities
    assert Capability.VISION not in classification.required_capabilities


def test_non_dict_parts_and_text_content_are_ignored() -> None:
    messages = [
        {"role": "user", "content": "plain"},
        {"role": "user", "content": ["not-a-dict"]},
    ]

    classification = _classify(messages=messages)

    assert classification.multimodal_required is False
    assert classification.required_capabilities == frozenset()
