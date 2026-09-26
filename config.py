"""
Configuration & LLM Management Module for Conversational Workflow Builder.
Supports OpenRouter, Groq, and OpenAI providers with automatic multi-model fallback execution.
"""

import os
from typing import List, Any, Type, Optional, Tuple
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# -------------------------------------------------------------
# Model Definitions & Fallback Priorities
# -------------------------------------------------------------
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")

OPENROUTER_FALLBACK_MODELS = [
    OPENROUTER_DEFAULT_MODEL,
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct",
    "openai/gpt-4o-mini"
]

GROQ_FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

OPENAI_FALLBACK_MODELS = [
    "gpt-4o-mini",
    "gpt-4o"
]


def get_provider_credentials() -> Tuple[str, str, List[str]]:
    """
    Identifies the configured LLM provider based on environment variables.
    Priority: OpenRouter > Groq > OpenAI
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key and openrouter_key.strip():
        os.environ["OPENAI_API_KEY"] = openrouter_key.strip()
        return "openrouter", openrouter_key.strip(), OPENROUTER_FALLBACK_MODELS
    elif groq_key and groq_key.strip():
        os.environ["OPENAI_API_KEY"] = groq_key.strip()
        return "groq", groq_key.strip(), GROQ_FALLBACK_MODELS
    elif openai_key and openai_key.strip():
        return "openai", openai_key.strip(), OPENAI_FALLBACK_MODELS
    else:
        raise ValueError(
            "No valid API key found in environment (.env). "
            "Please configure OPENROUTER_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY."
        )


def get_llm(model_name: Optional[str] = None, temperature: float = 0.0) -> ChatOpenAI:
    """
    Retrieves configured ChatOpenAI model using OpenRouter, Groq, or OpenAI endpoints with fallback chain.
    """
    provider, api_key, candidate_models = get_provider_credentials()
    target_model = model_name or candidate_models[0]

    base_url = None
    if provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "groq":
        base_url = "https://api.groq.com/openai/v1"

    kwargs = {
        "api_key": api_key,
        "model": target_model,
        "temperature": temperature,
        "max_retries": 2,
        "request_timeout": 30.0
    }
    if base_url:
        kwargs["base_url"] = base_url

    primary = ChatOpenAI(**kwargs)

    fallbacks = []
    for m in candidate_models:
        if m != target_model:
            fb_kwargs = dict(kwargs)
            fb_kwargs["model"] = m
            fallbacks.append(ChatOpenAI(**fb_kwargs))

    return primary.with_fallbacks(fallbacks) if fallbacks else primary


def invoke_structured_with_fallback(
    schema_cls: Type[Any],
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0
) -> Any:
    """
    Executes a structured output call across OpenRouter / Groq / OpenAI provider candidates.
    Auto-retries across candidate models on rate limits or API failures.
    """
    provider, api_key, candidate_models = get_provider_credentials()

    base_url = None
    if provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "groq":
        base_url = "https://api.groq.com/openai/v1"

    last_exception = None

    # De-duplicate candidate models while preserving order
    seen = set()
    unique_models = []
    for m in candidate_models:
        if m not in seen:
            seen.add(m)
            unique_models.append(m)

    for model_name in unique_models:
        try:
            kwargs = {
                "api_key": api_key,
                "model": model_name,
                "temperature": temperature,
                "max_retries": 2,
                "request_timeout": 30.0
            }
            if base_url:
                kwargs["base_url"] = base_url

            llm = ChatOpenAI(**kwargs)
            res = None

            try:
                structured_llm = llm.with_structured_output(schema_cls, method="function_calling")
                res = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
            except Exception:
                try:
                    structured_llm = llm.with_structured_output(schema_cls)
                    res = structured_llm.invoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt)
                    ])
                except Exception as e_inner:
                    raise e_inner

            if res is not None:
                return res
            else:
                print(f"[LLM Fallback Warning] Provider '{provider}' Model '{model_name}' returned None. Retrying next model...")

        except Exception as e:
            last_exception = e
            print(f"[LLM Fallback Warning] Provider '{provider}' Model '{model_name}' failed: {e}. Retrying next model...")
            continue

    raise RuntimeError(
        f"All LLM model fallbacks for provider '{provider}' ({', '.join(unique_models)}) failed. Last error: {str(last_exception)}"
    )
