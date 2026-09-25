"""
Caveman Memory Module for Conversation Context Reduction.

Applies Caveman style compression rules to historical conversation turns while:
1. Preserving all structured workflow parameters (emails, platforms, channels, repos, filters).
2. Preserving the latest user message without alteration.
3. Calculating exact token usage using tiktoken.
4. Providing graceful fallback handling on any error.
"""

import logging
import re
from typing import Any, Dict, List, Tuple

try:
    import tiktoken
    TOKENIZER = tiktoken.get_encoding("cl100k_base")
except Exception:
    TOKENIZER = None

logger = logging.getLogger(__name__)

# Common conversational filler words & preambles to strip in Caveman compression
FILLER_PATTERNS = [
    r"\b(hello|hi|hey|thanks|thank you|please|sure|okay|ok)\b",
    r"\b(could you|would you|can you|i would like to|i want to|i need to|please tell me|let me know)\b",
    r"\b(as an ai|i am an ai|assistant|sure thing|no problem)\b",
    r"\b(the|a|an)\b",
]

# Entity preservation regex (emails, channels, URLs, repos, handles, quoted strings)
ENTITY_PATTERN = re.compile(
    r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|"  # Email
    r"#\w+|"                                                   # Channel (#alerts)
    r"\b[A-Za-z0-9_]+/[A-Za-z0-9_-]+\b|"                      # GitHub repo (owner/repo)
    r"'[^']+'|\"[^\"]+\"|"                                     # Quoted strings
    r"\b(Slack|Gmail|Outlook|GitHub|Google Sheets|Discord|Teams|Webhook)\b)",  # Platforms
    re.IGNORECASE
)


def count_tokens(text: str) -> int:
    """Returns exact token count using tiktoken (or fallback word count approximation)."""
    if not text:
        return 0
    if TOKENIZER:
        try:
            return len(TOKENIZER.encode(text))
        except Exception:
            pass
    # Fallback approximation: ~1.3 tokens per word
    words = text.split()
    return int(len(words) * 1.3) or len(text) // 4


def compress_turn_content(content: str) -> str:
    """
    Compresses a single historical conversation turn using Caveman rules while preserving entity tokens.
    """
    if not content:
        return ""
    
    # 1. Find and preserve essential entity tokens (emails, channels, repo names, platforms)
    entities = ENTITY_PATTERN.findall(content)
    preserved_entities = set()
    for item in entities:
        if isinstance(item, tuple):
            for sub in item:
                if sub:
                    preserved_entities.add(sub.strip())
        elif item:
            preserved_entities.add(item.strip())

    # 2. Perform Caveman style text reduction
    reduced = content
    for pattern in FILLER_PATTERNS:
        reduced = re.sub(pattern, "", reduced, flags=re.IGNORECASE)

    # 3. Clean up whitespace
    reduced = re.sub(r"\s+", " ", reduced).strip()

    # 4. If reduction over-pruned essential entities, append them back
    missing_entities = [e for e in preserved_entities if e.lower() not in reduced.lower()]
    if missing_entities:
        reduced = f"{reduced} [{', '.join(missing_entities)}]"

    return reduced if reduced else content


def reduce_conversation_context(
    conversation_history: List[Dict[str, str]]
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """
    Applies Caveman context reduction to conversation history.

    Rules:
    - Never compresses or removes the latest turn (most recent user message).
    - Compresses older historical turns using Caveman rules.
    - Gracefully falls back to original history on error.
    - Returns reduced history list and detailed token metrics dictionary.
    """
    if not conversation_history:
        return [], {
            "original_tokens": 0,
            "reduced_tokens": 0,
            "tokens_saved": 0,
            "reduction_percentage": 0.0
        }

    try:
        # Calculate original tokens
        orig_str = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in conversation_history])
        orig_tokens = count_tokens(orig_str)

        if len(conversation_history) == 1:
            # Single turn: return untouched
            return list(conversation_history), {
                "original_tokens": orig_tokens,
                "reduced_tokens": orig_tokens,
                "tokens_saved": 0,
                "reduction_percentage": 0.0
            }

        # Separate historical turns from latest turn
        older_turns = conversation_history[:-1]
        latest_turn = conversation_history[-1]

        reduced_history: List[Dict[str, str]] = []
        for msg in older_turns:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            compressed_content = compress_turn_content(content)
            reduced_history.append({"role": role, "content": compressed_content})

        # Append latest turn untouched
        reduced_history.append(dict(latest_turn))

        # Calculate reduced tokens
        red_str = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in reduced_history])
        red_tokens = count_tokens(red_str)

        tokens_saved = max(0, orig_tokens - red_tokens)
        reduction_pct = round((tokens_saved / orig_tokens * 100), 2) if orig_tokens > 0 else 0.0

        metrics = {
            "original_tokens": orig_tokens,
            "reduced_tokens": red_tokens,
            "tokens_saved": tokens_saved,
            "reduction_percentage": reduction_pct
        }

        logger.info(
            f"[CAVEMAN MEMORY] Original: {orig_tokens} tokens | Reduced: {red_tokens} tokens | Saved: {tokens_saved} ({reduction_pct}%)"
        )
        print(f"[CAVEMAN MEMORY] Original: {orig_tokens} tokens | Reduced: {red_tokens} tokens | Saved: {tokens_saved} ({reduction_pct}%)")

        return reduced_history, metrics

    except Exception as exc:
        logger.warning(f"[CAVEMAN MEMORY ERROR] Context reduction failed: {exc}. Falling back to original history.")
        orig_tokens = len(orig_str.split()) if 'orig_str' in locals() and orig_str else 0
        return list(conversation_history), {
            "original_tokens": orig_tokens,
            "reduced_tokens": orig_tokens,
            "tokens_saved": 0,
            "reduction_percentage": 0.0,
            "error": str(exc)
        }
