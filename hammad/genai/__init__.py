"""hammad.genai"""

from typing import TYPE_CHECKING
from .._internal import create_getattr_importer


if TYPE_CHECKING:
    from .agents import (
        Agent,
        AgentEvent,
        AgentResponse,
        AgentStream,
        AgentContext,
        AgentMessages,
        AgentResponseChunk,
        create_agent,
    )
    from .agents.run import (
        run_agent,
        run_agent_iter,
        async_run_agent,
        async_run_agent_iter,
    )
    from .graphs import (
        GraphBuilder,
        GraphContext,
        GraphEnd,
        GraphEvent,
        GraphHistoryEntry,
        GraphNode,
        GraphState,
        GraphResponse,
        GraphStream,
        GraphResponseChunk,
        BaseGraph,
        BasePlugin,
        PluginDecorator,
        PydanticGraphContext,
        AudioPlugin,
        ServePlugin,
        MemoryPlugin,
        HistoryPlugin,
        SettingsPlugin,
        ActionNode,
        ActionInfo,
        ActionSettings,
        action,
        plugin,
    )
    from .models.embeddings import (
        Embedding,
        EmbeddingModel,
        EmbeddingModelResponse,
        EmbeddingModelSettings,
        run_embedding_model,
        async_run_embedding_model,
        create_embedding_model,
    )
    from .models.language import (
        LanguageModel,
        LanguageModelInstructorMode,
        LanguageModelMessages,
        LanguageModelName,
        LanguageModelRequest,
        LanguageModelResponse,
        LanguageModelResponseChunk,
        LanguageModelSettings,
        LanguageModelStream,
        run_language_model,
        async_run_language_model,
        create_language_model,
    )
    from .models.reranking import run_reranking_model, async_run_reranking_model
    from .models.multimodal import (
        run_image_edit_model,
        run_image_generation_model,
        run_image_variation_model,
        run_transcription_model,
        run_tts_model,
        async_run_image_edit_model,
        async_run_image_generation_model,
        async_run_image_variation_model,
        async_run_transcription_model,
        async_run_tts_model,
    )
    from .types.base import (
        BaseGenAIModel,
        BaseGenAIModelEvent,
        BaseGenAIModelResponse,
        BaseGenAIModelSettings,
        BaseGenAIModelStream,
    )
    from .types.history import History
    from .types.tools import (
        Tool,
        define_tool,
        execute_tools_from_language_model_response,
    )


__all__ = [
    # hammad.genai.agents.agent
    "Agent",
    "AgentEvent",
    "AgentResponse",
    "AgentStream",
    "AgentContext",
    "AgentMessages",
    "AgentResponseChunk",
    "create_agent",
    # hammad.genai.agents.run
    "run_agent",
    "run_agent_iter",
    "async_run_agent",
    "async_run_agent_iter",
    # hammad.genai.graphs
    "GraphBuilder",
    "GraphContext",
    "GraphEnd",
    "GraphEvent",
    "GraphHistoryEntry",
    "GraphNode",
    "GraphState",
    "GraphResponse",
    "GraphStream",
    "GraphResponseChunk",
    "BaseGraph",
    "BasePlugin",
    "PluginDecorator",
    "PydanticGraphContext",
    "AudioPlugin",
    "ServePlugin",
    "MemoryPlugin",
    "HistoryPlugin",
    "SettingsPlugin",
    "ActionNode",
    "ActionInfo",
    "ActionSettings",
    "action",
    "plugin",
    # hammad.genai.models.embeddings
    "Embedding",
    "EmbeddingModel",
    "EmbeddingModelResponse",
    "EmbeddingModelSettings",
    "run_embedding_model",
    "async_run_embedding_model",
    "create_embedding_model",
    # hammad.genai.models.language
    "LanguageModel",
    "LanguageModelInstructorMode",
    "LanguageModelMessages",
    "LanguageModelName",
    "LanguageModelRequest",
    "LanguageModelResponse",
    "LanguageModelResponseChunk",
    "LanguageModelSettings",
    "LanguageModelStream",
    "run_language_model",
    "async_run_language_model",
    "create_language_model",
    # hammad.genai.models.reranking
    "run_reranking_model",
    "async_run_reranking_model",
    # hammad.genai.models.multimodal
    "run_image_edit_model",
    "run_image_generation_model",
    "run_image_variation_model",
    "run_transcription_model",
    "run_tts_model",
    "async_run_image_edit_model",
    "async_run_image_generation_model",
    "async_run_image_variation_model",
    "async_run_transcription_model",
    "async_run_tts_model",
    # hammad.genai.types.base
    "BaseGenAIModel",
    "BaseGenAIModelEvent",
    "BaseGenAIModelResponse",
    "BaseGenAIModelSettings",
    "BaseGenAIModelStream",
    # hammad.genai.types.history
    "History",
    # hammad.genai.types.tools
    "Tool",
    "define_tool",
    "execute_tools_from_language_model_response",
]


__getattr__ = create_getattr_importer(__all__)


def __dir__() -> list[str]:
    return __all__
