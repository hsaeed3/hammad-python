"""ham.genai.models.language.types.language_model_name"""

from typing import (
    TypeAlias,
    Literal,
)


__all__ = [
    "LanguageModelName",
]


LanguageModelName: TypeAlias = Literal[
    "anthropic/claude-2.0",
    "anthropic/claude-2.1",
    "anthropic/claude-3-5-haiku-20241022",
    "anthropic/claude-3-5-haiku-latest",
    "anthropic/claude-3-5-sonnet-20240620",
    "anthropic/claude-3-5-sonnet-20241022",
    "anthropic/claude-3-5-sonnet-latest",
    "anthropic/claude-3-7-sonnet-20250219",
    "anthropic/claude-3-7-sonnet-latest",
    "anthropic/claude-3-haiku-20240307",
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-opus-latest",
    "anthropic/claude-3-sonnet-20240229",
    "anthropic/claude-4-opus-20250514",
    "anthropic/claude-4-sonnet-20250514",
    "anthropic/claude-opus-4-0",
    "anthropic/claude-opus-4-20250514",
    "anthropic/claude-sonnet-4-0",
    "anthropic/claude-sonnet-4-20250514",
    "bedrock/amazon.titan-tg1-large",
    "bedrock/amazon.titan-text-lite-v1",
    "bedrock/amazon.titan-text-express-v1",
    "bedrock/us.amazon.nova-pro-v1:0",
    "bedrock/us.amazon.nova-lite-v1:0",
    "bedrock/us.amazon.nova-micro-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "bedrock/anthropic.claude-instant-v1",
    "bedrock/anthropic.claude-v2:1",
    "bedrock/anthropic.claude-v2",
    "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/us.anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock/anthropic.claude-opus-4-20250514-v1:0",
    "bedrock/us.anthropic.claude-opus-4-20250514-v1:0",
    "bedrock/anthropic.claude-sonnet-4-20250514-v1:0",
    "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
    "bedrock/cohere.command-text-v14",
    "bedrock/cohere.command-r-v1:0",
    "bedrock/cohere.command-r-plus-v1:0",
    "bedrock/cohere.command-light-text-v14",
    "bedrock/meta.llama3-8b-instruct-v1:0",
    "bedrock/meta.llama3-70b-instruct-v1:0",
    "bedrock/meta.llama3-1-8b-instruct-v1:0",
    "bedrock/us.meta.llama3-1-8b-instruct-v1:0",
    "bedrock/meta.llama3-1-70b-instruct-v1:0",
    "bedrock/us.meta.llama3-1-70b-instruct-v1:0",
    "bedrock/meta.llama3-1-405b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-11b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-90b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-1b-instruct-v1:0",
    "bedrock/us.meta.llama3-2-3b-instruct-v1:0",
    "bedrock/us.meta.llama3-3-70b-instruct-v1:0",
    "bedrock/mistral.mistral-7b-instruct-v0:2",
    "bedrock/mistral.mixtral-8x7b-instruct-v0:1",
    "bedrock/mistral.mistral-large-2402-v1:0",
    "bedrock/mistral.mistral-large-2407-v1:0",
    "claude-2.0",
    "claude-2.1",
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku-latest",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet-latest",
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229",
    "claude-3-opus-latest",
    "claude-3-sonnet-20240229",
    "claude-4-opus-20250514",
    "claude-4-sonnet-20250514",
    "claude-opus-4-0",
    "claude-opus-4-20250514",
    "claude-sonnet-4-0",
    "claude-sonnet-4-20250514",
    "cohere/c4ai-aya-expanse-32b",
    "cohere/c4ai-aya-expanse-8b",
    "cohere/command",
    "cohere/command-light",
    "cohere/command-light-nightly",
    "cohere/command-nightly",
    "cohere/command-r",
    "cohere/command-r-03-2024",
    "cohere/command-r-08-2024",
    "cohere/command-r-plus",
    "cohere/command-r-plus-04-2024",
    "cohere/command-r-plus-08-2024",
    "cohere/command-r7b-12-2024",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
    "google-gla/gemini-2.0-flash",
    "google-gla/gemini-2.0-flash-lite",
    "google-gla/gemini-2.5-flash",
    "google-gla/gemini-2.5-flash-lite-preview-06-17",
    "google-gla/gemini-2.5-pro",
    "google-vertex/gemini-2.0-flash",
    "google-vertex/gemini-2.0-flash-lite",
    "google-vertex/gemini-2.5-flash",
    "google-vertex/gemini-2.5-flash-lite-preview-06-17",
    "google-vertex/gemini-2.5-pro",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0125-preview",
    "gpt-4-0314",
    "gpt-4-0613",
    "gpt-4-1106-preview",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-4-32k-0613",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-turbo-preview",
    "gpt-4-vision-preview",
    "gpt-4.1",
    "gpt-4.1-2025-04-14",
    "gpt-4.1-mini",
    "gpt-4.1-mini-2025-04-14",
    "gpt-4.1-nano",
    "gpt-4.1-nano-2025-04-14",
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-11-20",
    "gpt-4o-audio-preview",
    "gpt-4o-audio-preview-2024-10-01",
    "gpt-4o-audio-preview-2024-12-17",
    "gpt-4o-audio-preview-2025-06-03",
    "gpt-4o-mini",
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-mini-audio-preview",
    "gpt-4o-mini-audio-preview-2024-12-17",
    "gpt-4o-mini-search-preview",
    "gpt-4o-mini-search-preview-2025-03-11",
    "gpt-4o-search-preview",
    "gpt-4o-search-preview-2025-03-11",
    "groq/gemma2-9b-it",
    "groq/llama-3.3-70b-versatile",
    "groq/llama-3.1-8b-instant",
    "groq/llama-guard-3-8b",
    "groq/llama3-70b-8192",
    "groq/llama3-8b-8192",
    "groq/moonshotai/kimi-k2-instruct",
    "groq/whisper-large-v3",
    "groq/whisper-large-v3-turbo",
    "groq/playai-tts",
    "groq/playai-tts-arabic",
    "groq/qwen-qwq-32b",
    "groq/mistral-saba-24b",
    "groq/qwen-2.5-coder-32b",
    "groq/qwen-2.5-32b",
    "groq/distil-whisper-large-v3-en",
    "groq/deepseek-r1-distill-qwen-32b",
    "groq/deepseek-r1-distill-llama-70b",
    "groq/llama-3.3-70b-specdec",
    "groq/llama-3.2-1b-preview",
    "groq/llama-3.2-3b-preview",
    "groq/llama-3.2-11b-vision-preview",
    "groq/llama-3.2-90b-vision-preview",
    "heroku/claude-3-5-haiku",
    "heroku/claude-3-5-sonnet-latest",
    "heroku/claude-3-7-sonnet",
    "heroku/claude-4-sonnet",
    "heroku/claude-3-haiku",
    "huggingface/Qwen/QwQ-32B",
    "huggingface/Qwen/Qwen2.5-72B-Instruct",
    "huggingface/Qwen/Qwen3-235B-A22B",
    "huggingface/Qwen/Qwen3-32B",
    "huggingface/deepseek-ai/DeepSeek-R1",
    "huggingface/meta-llama/Llama-3.3-70B-Instruct",
    "huggingface/meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    "huggingface/meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "mistral/codestral-latest",
    "mistral/mistral-large-latest",
    "mistral/mistral-moderation-latest",
    "mistral/mistral-small-latest",
    "o1",
    "o1-2024-12-17",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1-preview",
    "o1-preview-2024-09-12",
    "o1-pro",
    "o1-pro-2025-03-19",
    "o3",
    "o3-2025-04-16",
    "o3-deep-research",
    "o3-deep-research-2025-06-26",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o3-pro",
    "o3-pro-2025-06-10",
    "openai/chatgpt-4o-latest",
    "openai/codex-mini-latest",
    "openai/gpt-3.5-turbo",
    "openai/gpt-3.5-turbo-0125",
    "openai/gpt-3.5-turbo-0301",
    "openai/gpt-3.5-turbo-0613",
    "openai/gpt-3.5-turbo-1106",
    "openai/gpt-3.5-turbo-16k",
    "openai/gpt-3.5-turbo-16k-0613",
    "openai/gpt-4",
    "openai/gpt-4-0125-preview",
    "openai/gpt-4-0314",
    "openai/gpt-4-0613",
    "openai/gpt-4-1106-preview",
    "openai/gpt-4-32k",
    "openai/gpt-4-32k-0314",
    "openai/gpt-4-32k-0613",
    "openai/gpt-4-turbo",
    "openai/gpt-4-turbo-2024-04-09",
    "openai/gpt-4-turbo-preview",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4.1",
    "openai/gpt-4.1-2025-04-14",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1-mini-2025-04-14",
    "openai/gpt-4.1-nano",
    "openai/gpt-4.1-nano-2025-04-14",
    "openai/gpt-4o",
    "openai/gpt-4o-2024-05-13",
    "openai/gpt-4o-2024-08-06",
    "openai/gpt-4o-2024-11-20",
    "openai/gpt-4o-audio-preview",
    "openai/gpt-4o-audio-preview-2024-10-01",
    "openai/gpt-4o-audio-preview-2024-12-17",
    "openai/gpt-4o-audio-preview-2025-06-03",
    "openai/gpt-4o-mini",
    "openai/gpt-4o-mini-2024-07-18",
    "openai/gpt-4o-mini-audio-preview",
    "openai/gpt-4o-mini-audio-preview-2024-12-17",
    "openai/gpt-4o-mini-search-preview",
    "openai/gpt-4o-mini-search-preview-2025-03-11",
    "openai/gpt-4o-search-preview",
    "openai/gpt-4o-search-preview-2025-03-11",
    "openai/o1",
    "openai/o1-2024-12-17",
    "openai/o1-mini",
    "openai/o1-mini-2024-09-12",
    "openai/o1-preview",
    "openai/o1-preview-2024-09-12",
    "openai/o1-pro",
    "openai/o1-pro-2025-03-19",
    "openai/o3",
    "openai/o3-2025-04-16",
    "openai/o3-deep-research",
    "openai/o3-deep-research-2025-06-26",
    "openai/o3-mini",
    "openai/o3-mini-2025-01-31",
    "openai/o4-mini",
    "openai/o4-mini-2025-04-16",
    "openai/o4-mini-deep-research",
    "openai/o4-mini-deep-research-2025-06-26",
    "openai/o3-pro",
    "openai/o3-pro-2025-06-10",
    "openai/computer-use-preview",
    "openai/computer-use-preview-2025-03-11",
    "xai/grok-4",
    "xai/grok-4-0709",
    "xai/grok-3",
    "xai/grok-3-mini",
    "xai/grok-3-fast",
    "xai/grok-3-mini-fast",
    "xai/grok-2-vision-1212",
    "xai/grok-2-image-1212",
    "test",
]


"""Known model names that can be used with the `model` parameter of [`Agent`][pydantic_ai.Agent].

`KnownModelName` is provided as a concise way to specify a model.
"""
