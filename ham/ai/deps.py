"""ham.ai.deps

Helper functions and resources used interally to manage the client usage and dependencies
from the OpenAI, LiteLLM and Instructor SDKs.

These resources provide access to the direct LiteLLM API, as well as cached creation of OpenAI
and Instructor clients.
"""

from typing import TypeAlias, Literal, Tuple
from dataclasses import dataclass, field
from functools import lru_cache, cached_property
import inspect
from importlib.util import find_spec
import os

from instructor.core.client import (
    from_openai,
    from_litellm,
    AsyncInstructor
)
from instructor.mode import Mode as InstructorMode

from openai import AsyncOpenAI
from openai.types.chat_model import ChatModel as OpenAIChatModel
from openai.types.embedding_model import EmbeddingModel as OpenAIEmbeddingModel


OpenAIClientCacheKey : TypeAlias = Tuple[Literal["openai"], str]
"""Type alias for the cache key format used to cache OpenAI clients based on provider
or a custom base URL.
"""


InstructorClientCacheKey : TypeAlias = Tuple[
    Tuple[Literal["openai", "litellm"], str | Literal["litellm"]], InstructorMode
]
"""Type alias for the cache key format used to cache Instructor clients based on provider
(for OpenAI clients) along with Instructor mode.

NOTE: LiteLLM clients are only cached based on mode, as `hammad-python` interacts with
LiteLLM as a singleton interface."""


KNOWN_OPENAI_CHAT_MODELS: frozenset[str] = frozenset(OpenAIChatModel.__args__)
"""Direct provided chat model names from the OpenAI SDK."""


KNOWN_OPENAI_EMBEDDING_MODELS: frozenset[str] = frozenset(OpenAIEmbeddingModel.__args__)
"""Direct provided embedding model names from the OpenAI SDK."""


KNOWN_OPENAI_PROVIDER_PREFIXES : frozenset[str] = frozenset({
    "openai", "ollama", "openrouter", "groq", "xai", "lm_studio"
})
"""Simple definition of 'known' OpenAI provider prefixes when calling generative AI
models. Although more providers are compatible with the OpenAI specification, the library
chooses to let them fallback directly to LiteLLM."""


KNOWN_OPENAI_PROVIDER_CONFIGS : dict[str, dict[str, str]] = {
    # note: openai is excluded as we use 'raw' config
    "openrouter" : {
        "base_url" : "https://openrouter.ai/api/v1",
        "api_key_env" : "OPENROUTER_API_KEY"
    },
    "ollama" : {
        "base_url" : "http://localhost:11434/v1",
        "api_key_env" : "OLLAMA_API_KEY",
        "api_key_default" : "ollama"
    },
    "groq" : {
        "base_url" : "https://api.groq.com/openai/v1",
        "api_key_env" : "GROQ_API_KEY"
    },
    "xai" : {
        "base_url" : "https://api.x.ai/v1",
        "api_key_env" : "XAI_API_KEY"
    },
    "lm_studio" : {
        "base_url" : "http://localhost:1234/v1",
        "api_key_env" : "LM_STUDIO_API_KEY",
        "api_key_default" : "lm_studio"
    }
}
"""Predefined provider configurations for known OpenAI-compatible providers."""


KNOWN_OPENAI_CLIENT_PARAMS : set = set(inspect.signature(AsyncOpenAI.__init__).parameters.keys())
"""Set of valid parameter names for the AsyncOpenAI client initialization."""
KNOWN_OPENAI_CLIENT_PARAMS.discard("self")


@lru_cache()
def get_openai_model_key(
    model : str | None = None,
    base_url : str | None = None
) -> OpenAIClientCacheKey | Literal["litellm"]:
    """Helper function used both to determine if a moel is compatible with the OpenAI
    provider, as well as to generate a cache key for a specific OpenAI configuration."""

    if base_url is not None:
        return ("openai", base_url)
    if model is None and base_url is None:
        raise ValueError("Either model or base_url must be provided to determine OpenAI client key.")
    if any((
        model in KNOWN_OPENAI_CHAT_MODELS,
        model in KNOWN_OPENAI_EMBEDDING_MODELS,
    )):
        return ("openai", "openai")
    for prefix in KNOWN_OPENAI_PROVIDER_PREFIXES:
        if model.startswith(prefix):
            return ("openai", prefix)       
    else:
        return "litellm"
    

@lru_cache()
def get_openai_client_config(
    key : OpenAIClientCacheKey,
    config : tuple[tuple[str, object], ...] | None = None
) -> dict[str, object]:
    """Helper function used to retrieve or format 'default'/'predefined' OpenAI client
    provider confgurations based on a cache key.
    
    Expects 'config' to be a hashable tuple of (key, value) pairs.
    """
    
    # 1. Convert hashable tuple back to dict
    user_config: dict[str, object] = dict(config) if config else {}
    provider_name = key[1]

    # 2. Handle pass-through cases (default 'openai' or custom base_url)
    if provider_name == "openai" or provider_name not in KNOWN_OPENAI_PROVIDER_CONFIGS:
        merged_config = user_config
    
    # 3. Handle known provider logic
    else:
        provider_defaults = KNOWN_OPENAI_PROVIDER_CONFIGS[provider_name]
        
        # Start with user_config, so its values take precedence
        merged_config = dict(user_config)

        # Set base_url from defaults ONLY if not provided by user
        if 'base_url' not in merged_config:
            merged_config['base_url'] = provider_defaults['base_url']

        # Set api_key from defaults ONLY if not provided by user
        if 'api_key' not in merged_config:
            api_key = (
                os.getenv(provider_defaults["api_key_env"]) or 
                provider_defaults.get("api_key_default")
            )
            if api_key:
                merged_config['api_key'] = api_key
    
    # 4. Use inspect to filter for valid AsyncOpenAI init args
    valid_params = KNOWN_OPENAI_CLIENT_PARAMS

    filtered_config = {
        k: v for k, v in merged_config.items() if k in valid_params
    }
    
    return filtered_config


@dataclass
class AIDeps:
    """Singleton interface used internally by the `hammad-python` framework to manage and
    cache various AI backend client resources.
    """

    _instance = None
    """Internal singleton instance reference."""

    _litellm = None
    """Singleton reference to the LiteLLM library"""

    OPENAI_CLIENT_CACHE : dict[OpenAIClientCacheKey, AsyncOpenAI] = field(
        default_factory=dict
    )
    """Cache of created OpenAI clients based on provider or custom base URL."""

    INSTRUCTOR_CLIENT_CACHE : dict[InstructorClientCacheKey, AsyncInstructor] = field(
        default_factory=dict
    )
    """Cache of created Instructor clients based on provider (for OpenAI) and mode."""

    @property
    def LITELLM(self):
        return self._litellm
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AIDeps, cls).__new__(cls)
        return cls._instance
    
    @cached_property
    def litellm_available(self) -> bool:
        return find_spec("litellm") is not None
    
    @property
    def litellm_loaded(self) -> bool:
        return self._litellm is not None
    
    @classmethod
    def load_litellm(cls):
        if not cls().litellm_available:
            raise ImportError("LiteLLM library is not available. Please install it to use LiteLLM features.")
        if cls()._litellm is None:
            try:
                import litellm
                litellm.drop_params = True
                litellm.modify_params = True
                cls()._litellm = litellm
            except ImportError:
                raise ImportError(
                    "The `litellm` library is required to use non-OpenAI model providers.\n",
                    "Please install it with either:\n",
                    "    `pip install litellm` or\n",
                    "    `pip install 'hammad-python[litellm]'`"
                )
            cls()._litellm = litellm

    @classmethod
    def get_litellm(cls):
        """Get the singleton instance of the LiteLLM library after importing it if needed."""
        if not cls().litellm_loaded:
            cls.load_litellm()
        return cls()._litellm
    
    def get_openai_client(
        self,
        model : str | None = None,
        base_url : str | None = None,
        api_key : str | None = None,
        **kwargs
    ) -> AsyncOpenAI:
        cache_key = get_openai_model_key(
            model = model,
            base_url = base_url
        )
        if cache_key[0] != "openai":
            raise ValueError("Requested model is not compatible with OpenAI provider.")
        
        if cache_key in self.OPENAI_CLIENT_CACHE:
            return self.OPENAI_CLIENT_CACHE[cache_key]
        
        base_config = tuple(kwargs.items())
        if api_key is not None:
            base_config += (("api_key", api_key),)
        if base_url is not None:
            base_config += (("base_url", base_url),)

        try:
            client = AsyncOpenAI(
            **get_openai_client_config(
                key = cache_key,
                config = base_config
            )
            )
            self.OPENAI_CLIENT_CACHE[cache_key] = client
            return client
        except Exception as e:
            raise RuntimeError(f"Failed to create OpenAI client for model {model}: {e}") from e
        
    def get_instructor_client(
        self,
        key : OpenAIClientCacheKey | Literal["litellm"],
        instructor_mode : InstructorMode = InstructorMode.TOOLS
    ) -> AsyncInstructor:
        
        cache_key = (key, instructor_mode)

        if cache_key in self.INSTRUCTOR_CLIENT_CACHE:
            return self.INSTRUCTOR_CLIENT_CACHE[cache_key]
        
        if key == "litellm" or self.litellm_loaded:
            litellm = self.get_litellm()
            instructor_client = from_litellm(
                completion=litellm.acompletion, 
                mode=instructor_mode
            )

        elif isinstance(key, tuple) and key[0] == "openai":
            if key not in self.OPENAI_CLIENT_CACHE:
                raise ValueError(
                    "OpenAI client must be created before creating Instructor client.\n"
                    "Please call `get_openai_client` first."
                )
            instructor_client = from_openai(
                openai=self.OPENAI_CLIENT_CACHE[key],
                mode=instructor_mode
            )
        else:
            raise ValueError("Invalid key provided for Instructor client creation.")

        self.INSTRUCTOR_CLIENT_CACHE[cache_key] = instructor_client
        return instructor_client
