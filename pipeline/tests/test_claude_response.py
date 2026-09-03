"""Tests for safe extraction of Messages API responses.

Pins the 2026-09-03 refresh failure: a safety decline returns HTTP 200 with an
empty content list, so `message.content[0].text` raised IndexError.
"""
import pytest

import claude_response as cr


# ── TEST DOUBLES ─────────────────────────────────────────────────────────────
class _Block:
    def __init__(self, text: str, type_: str = "text"):
        self.text = text
        self.type = type_


class _Usage:
    def __init__(self, output_tokens: int):
        self.output_tokens = output_tokens


class _Details:
    def __init__(self, category=None, explanation=None):
        self.type = "refusal"
        self.category = category
        self.explanation = explanation


class _Message:
    def __init__(self, content=None, stop_reason="end_turn", usage=None, stop_details=None):
        self.content = content if content is not None else []
        self.stop_reason = stop_reason
        if usage is not None:
            self.usage = usage
        if stop_details is not None:
            self.stop_details = stop_details


# ── THE PRODUCTION FAILURE ───────────────────────────────────────────────────
def test_refusal_raises_declined_not_index_error():
    # Real shape of the 09-03 failure: 200 OK, refusal, empty content, 0 tokens.
    msg = _Message(content=[], stop_reason="refusal", usage=_Usage(0))
    with pytest.raises(cr.ClaudeDeclined):
        cr.extract_text(msg, context="When Code Meets the Genome")


def test_refusal_message_names_the_article_and_category():
    msg = _Message(
        content=[], stop_reason="refusal", usage=_Usage(0),
        stop_details=_Details(category="bio", explanation="declined"),
    )
    with pytest.raises(cr.ClaudeDeclined) as exc:
        cr.extract_text(msg, context="When Code Meets the Genome")
    text = str(exc.value)
    assert "When Code Meets the Genome" in text
    assert "bio" in text


def test_refusal_without_stop_details_still_raises_cleanly():
    # stop_details only exists on Opus 4.7+; these pipelines run sonnet-4-5.
    msg = _Message(content=[], stop_reason="refusal", usage=_Usage(0))
    with pytest.raises(cr.ClaudeDeclined) as exc:
        cr.extract_text(msg)
    assert "declined" in str(exc.value).lower()


def test_empty_content_without_refusal_raises_empty_response():
    msg = _Message(content=[], stop_reason="end_turn", usage=_Usage(0))
    with pytest.raises(cr.ClaudeEmptyResponse):
        cr.extract_text(msg)


def test_content_with_no_text_block_raises_empty_response():
    msg = _Message(content=[_Block("", type_="thinking")], stop_reason="end_turn")
    with pytest.raises(cr.ClaudeEmptyResponse):
        cr.extract_text(msg)


# ── THE HAPPY PATH MUST BE UNCHANGED ─────────────────────────────────────────
def test_normal_response_returns_the_text():
    msg = _Message(content=[_Block("# Title\n\nBody text.")], usage=_Usage(1234))
    assert cr.extract_text(msg) == "# Title\n\nBody text."


def test_multiple_text_blocks_are_concatenated():
    msg = _Message(content=[_Block("first "), _Block("second")])
    assert cr.extract_text(msg) == "first second"


def test_non_text_blocks_are_ignored():
    msg = _Message(content=[_Block("x", type_="thinking"), _Block("real text")])
    assert cr.extract_text(msg) == "real text"


def test_max_tokens_still_returns_the_partial_text(capsys):
    msg = _Message(content=[_Block("cut off here")], stop_reason="max_tokens")
    assert cr.extract_text(msg) == "cut off here"
    assert "max_tokens" in capsys.readouterr().out


# ── TOKEN ACCOUNTING ─────────────────────────────────────────────────────────
def test_output_tokens_reads_usage():
    assert cr.output_tokens(_Message(usage=_Usage(4321)), 6000) == 4321


def test_output_tokens_falls_back_when_usage_absent():
    assert cr.output_tokens(_Message(), 6000) == 6000


def test_declined_call_reports_zero_tokens():
    # Anthropic does not bill a decline that produced no output, so 0 is right
    # — and it is what the 09-03 log showed ("0/80,000 tokens").
    assert cr.output_tokens(_Message(usage=_Usage(0)), 6000) == 0
