"""hammad.genai.embedding_models.embedding_model_name"""

from typing import Literal


__all__ = ("EmbeddingModelName",)


EmbeddingModelName = Literal[
    # OpenAI Embedding Models
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
    # OpenAI Compatible Embedding Models
    "openai/text-embedding-3-small",
    "openai/text-embedding-3-large",
    "openai/text-embedding-ada-002",
    # Bedrock Embedding Models
    "amazon.titan-embed-text-v1",
    "cohere.embed-english-v3",
    "cohere.embed-multilingual-v3",
    # Cohere Embedding Models
    "embed-english-v3.0",
    "embed-english-light-v3.0",
    "embed-multilingual-v3.0",
    "embed-multilingual-light-v3.0",
    "embed-english-v2.0",
    "embed-english-light-v2.0",
    "embed-multilingual-v2.0",
    # NVIDIA NIM Embedding Models
    "nvidia_nim/NV-Embed-QA",
    "nvidia_nim/nvidia/nv-embed-v1",
    "nvidia_nim/nvidia/nv-embedqa-mistral-7b-v2",
    "nvidia_nim/nvidia/nv-embedqa-e5-v5",
    "nvidia_nim/nvidia/embed-qa-4",
    "nvidia_nim/nvidia/llama-3.2-nv-embedqa-1b-v1",
    "nvidia_nim/nvidia/llama-3.2-nv-embedqa-1b-v2",
    "nvidia_nim/snowflake/arctic-embed-l",
    "nvidia_nim/baai/bge-m3",
    # HuggingFace Embedding Models
    "huggingface/microsoft/codebert-base",
    "huggingface/BAAI/bge-large-zh",
    # Mistral AI Embedding Models
    "mistral/mistral-embed",
    # Gemini AI Embedding Models
    "gemini/text-embedding-004",
    # Vertex AI Embedding Models
    "vertex_ai/textembedding-gecko",
    "vertex_ai/textembedding-gecko-multilingual",
    "vertex_ai/textembedding-gecko-multilingual@001",
    "vertex_ai/textembedding-gecko@001",
    "vertex_ai/textembedding-gecko@003",
    "vertex_ai/text-embedding-preview-0409",
    "vertex_ai/text-multilingual-embedding-preview-0409",
    # Voyage AI Embedding Models
    "voyage/voyage-01",
    "voyage/voyage-lite-01",
    "voyage/voyage-lite-01-instruct",
    # Nebius AI Studio Embedding Models
    "nebius/BAAI/bge-en-icl",
    "nebius/BAAI/bge-multilingual-gemma2",
    "nebius/intfloat/e5-mistral-7b-instruct",
    # Ollama Embedding Models
    "ollama/granite-embedding:30m",
    "ollama/granite-embedding:278m",
    "ollama/snowflake-arctic-embed2",
    "ollama/bge-large",
    "ollama/paraphrase-multilingual",
    "ollama/bge-m3",
    "ollama/snowflake-arctic-embed",
    "ollama/mxbai-embed-large",
    "ollama/all-minilm",
    "ollama/nomic-embed-text",
]
"""Common embedding models supported by `litellm`."""
