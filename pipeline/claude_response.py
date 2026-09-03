"""
Safe extraction of text from an Anthropic Messages API response.

Why this exists
---------------
Four call sites did `message.content[0].text` directly. That assumes the
response always carries at least one content block, which is not true: when a
safety classifier declines a request the API returns **HTTP 200** — no
exception is raised — with `stop_reason: "refusal"`, an **empty** `content`
list, and `usage.output_tokens: 0`.

That is exactly what happened on 2026-09-03. The content refresh picked two
June articles about synthetic-DNA monitoring, both were declined (the refusal
categories include "bio"), and `content[0]` raised

    ❌ Refresh failed: list index out of range

twice, burning two of the twelve Claude calls for the run and reporting a
generic IndexError that says nothing about the real cause. The third article
that run — same age, no biology in it — refreshed normally.

So: always check `stop_reason` before reading `content`.

`stop_details` (with the refusal `category` and `explanation`) is populated
only on Opus 4.7 and later; these pipelines run claude-sonnet-4-5, so it is
read defensively and the code never depends on it being there.
"""


class ClaudeDeclined(Exception):
    """The model declined the request. Retrying the same prompt will not help."""


class ClaudeEmptyResponse(Exception):
    """A 200 response that carried no usable text block."""


def extract_text(message, context: str = "") -> str:
    """Return the concatenated text of a Messages API response.

    Raises
    ------
    ClaudeDeclined      — stop_reason == "refusal"
    ClaudeEmptyResponse — no text block in the response

    Both carry a message naming ``context`` so the run log says which article
    was involved instead of just "list index out of range".
    """
    where = f" [{context}]" if context else ""

    stop_reason = getattr(message, "stop_reason", None)
    if stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        category = getattr(details, "category", None) if details else None
        explanation = getattr(details, "explanation", None) if details else None
        parts = [f"Claude declined this request{where}"]
        if category:
            parts.append(f"category={category}")
        if explanation:
            parts.append(str(explanation)[:200])
        raise ClaudeDeclined(" — ".join(parts))

    blocks = getattr(message, "content", None) or []
    text = "".join(
        getattr(b, "text", "") for b in blocks if getattr(b, "type", None) == "text"
    ).strip()

    if not text:
        raise ClaudeEmptyResponse(
            f"Claude returned no text block{where} (stop_reason={stop_reason!r}, "
            f"{len(blocks)} content block(s))"
        )

    # Not fatal — the caller's own truncation checks decide what to do with a
    # cut-off article — but it belongs in the log, because a silently truncated
    # article otherwise just looks like a short one.
    if stop_reason == "max_tokens":
        print(f"  ⚠️  Response hit max_tokens{where} — output may be cut off")

    return text


def output_tokens(message, default: int) -> int:
    """usage.output_tokens, or ``default`` when the field is absent.

    A declined request reports 0 here, which is correct — Anthropic does not
    bill a decline that produced no output.
    """
    usage = getattr(message, "usage", None)
    if usage is None:
        return default
    return getattr(usage, "output_tokens", default)
