"""Anthropic API wrapper with retry, rate limiting, and response caching."""

import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from src.common.io import is_cached, load_json, save_json

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in environment or .env file")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True,
)
def call_claude(
    prompt: str,
    system: str = "",
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
    cache_path: Path | None = None,
    force: bool = False,
) -> str:
    """Call Claude with optional file-level caching. Returns response text."""
    if cache_path and not force and is_cached(cache_path):
        cached = load_json(cache_path)
        if cached and "response" in cached:
            return cached["response"]

    client = get_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    text = response.content[0].text

    if cache_path:
        save_json({"response": text, "model": model, "prompt_preview": prompt[:200]}, cache_path)

    return text


def call_claude_json(
    prompt: str,
    system: str = "",
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
    cache_path: Path | None = None,
    force: bool = False,
) -> dict | None:
    """Call Claude and parse JSON response. Returns None on parse failure."""
    import json

    raw = call_claude(
        prompt=prompt,
        system=system,
        model=model,
        max_tokens=max_tokens,
        cache_path=cache_path,
        force=force,
    )

    # Extract JSON from response even if wrapped in markdown code fences
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first { ... } block
        import re
        match = re.search(r"\{[\s\S]+\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def batch_call_claude(
    items: list[dict],
    prompt_fn,
    cache_dir: Path,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
    requests_per_minute: int = 40,
    force: bool = False,
) -> list[dict]:
    """
    Run LLM analysis over a list of items with rate limiting and per-item caching.

    items: list of dicts passed to prompt_fn
    prompt_fn: callable(item) -> (system_str, user_str, cache_filename)
    Returns items with "llm_result" key added.
    """
    results = []
    delay = 60.0 / requests_per_minute

    for i, item in enumerate(items):
        system, user, cache_name = prompt_fn(item)
        cp = cache_dir / cache_name

        try:
            result = call_claude_json(
                prompt=user,
                system=system,
                model=model,
                max_tokens=max_tokens,
                cache_path=cp,
                force=force,
            )
            item = dict(item)
            item["llm_result"] = result
            item["llm_error"] = None
        except Exception as e:
            item = dict(item)
            item["llm_result"] = None
            item["llm_error"] = str(e)

        results.append(item)

        if i < len(items) - 1:
            time.sleep(delay)

    return results
