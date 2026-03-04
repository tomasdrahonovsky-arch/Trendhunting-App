"""Claude API interaction with retry logic."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import anthropic
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int


@retry(
    retry=retry_if_exception_type(
        (anthropic.RateLimitError, anthropic.InternalServerError)
    ),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def call_claude(system: str, user: str, max_tokens: int = 4096) -> LLMResponse:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    logger.info("Calling Claude %s...", CLAUDE_MODEL)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    content = response.content[0].text if response.content else ""
    logger.info(
        "Claude response — tokens in=%d out=%d",
        response.usage.input_tokens,
        response.usage.output_tokens,
    )

    return LLMResponse(
        content=content,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
