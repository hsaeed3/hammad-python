"""hammad.ai.models.embeddings"""

from typing import Any, List, Optional, Union

from ...based.model import BasedModel
from ...based.fields import basedfield
from ...text import convert_to_text
from ._providers import get_litellm_module

try:
    from fastembed import TextEmbedding as FastTextEmbedding
    from fastembed import SparseTextEmbedding as FastSparseTextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False


class Embedding(BasedModel):
    """Simple embedding object with embedding at top level."""
    
    embedding: List[float] = basedfield(description="The embedding vector")


class EmbeddingData(BasedModel):
    """Represents a single embedding data point."""
    
    embedding: List[float] = basedfield(description="The embedding vector")
    index: int = basedfield(description="The index of this embedding in the input")
    object: str = basedfield(default="embedding", description="The object type")


class EmbeddingUsage(BasedModel):
    """Usage statistics for embedding requests."""
    
    prompt_tokens: int = basedfield(description="Number of tokens in the input")
    total_tokens: int = basedfield(description="Total number of tokens used")


class Embedding(BasedModel, kw_only = True):
    """Response from embedding API calls."""
    
    model: str = basedfield(description="The model used for embeddings")
    object: str = basedfield(default="list", description="The object type")
    dimensions : int = basedfield(description="The dimensions of the embedding")
    data: List[EmbeddingData] = basedfield(description="List of embedding data")
    usage: EmbeddingUsage = basedfield(description="Usage statistics")


class EmbeddingModel:
    """Functional class for creating embeddings using various
    embedding models. This module utilizes `litellm` for the
    embedding client and `fastembed` for local embeddings."""

    def __init__(
        self,
        model : str,
    ) -> None:
        self.model = model
        self._fastembed_client = None
        self._is_fastembed = model.startswith("fastembed/")
        self._is_sparse = False
        
        if self._is_fastembed:
            self._init_fastembed()
    
    def _init_fastembed(self):
        """Initialize fastembed client."""
        if not FASTEMBED_AVAILABLE:
            raise ImportError(
                "fastembed is required for fastembed models. "
                "Install with: pip install fastembed"
            )
        
        # Extract actual model name (remove fastembed/ prefix)
        model_name = self.model[9:]  # Remove "fastembed/"
        
        # Check if it's a sparse model
        if model_name.startswith("sparse/"):
            self._is_sparse = True
            model_name = model_name[7:]  # Remove "sparse/"
            self._fastembed_client = FastSparseTextEmbedding(model_name)
        else:
            self._fastembed_client = FastTextEmbedding(model_name)

    @staticmethod
    async def async_embed(
        model : str = "openai/text-embedding-3-small",
        input=[],
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600, 
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        caching: bool = False,
        user: Optional[str] = None,
        format : bool = False,
    ) -> Embedding:
        """Create an embedding for the given text."""
        # Check if it's a fastembed model
        if model.startswith("fastembed/"):
            return await EmbeddingModel._fastembed_embed(
                model=model,
                input=input,
                format=format
            )
        
        litellm_module = get_litellm_module()

        processed_input = []
        for text in input:
            if not isinstance(text, str) and format:
                processed_input.append(convert_to_text(text))
            else:
                processed_input.append(text)

        try:
            response = await litellm_module.aembedding(
                model = model,
                input = processed_input,
                dimensions = dimensions,
                encoding_format = encoding_format,
                timeout = timeout,
                api_base = api_base,
                api_version = api_version,
                api_key = api_key,
                api_type = api_type,
                caching = caching,
                user = user,
            )
            
            # Convert litellm response to our BasedModel format
            embedding_data = []
            for i, item in enumerate(response.data):
                embedding_data.append(EmbeddingData(
                    embedding=item['embedding'],
                    index=i,
                    object="embedding"
                ))
            
            usage = EmbeddingUsage(
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            return Embedding(
                data=embedding_data,
                model=response.model,
                object="list",
                usage=usage
            )
            
        except Exception as e:
            raise e
    
    @staticmethod
    def embed(
        model : str = "openai/text-embedding-3-small",
        input=[],
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
        timeout=600, 
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        caching: bool = False,
        user: Optional[str] = None,
        format : bool = False,
    ) -> Embedding:
        """Create an embedding for the given text."""
        # Check if it's a fastembed model
        if model.startswith("fastembed/"):
            return EmbeddingModel._fastembed_embed_sync(
                model=model,
                input=input,
                format=format
            )
        
        litellm_module = get_litellm_module()

        processed_input = []
        for text in input:
            if not isinstance(text, str) and format:
                processed_input.append(convert_to_text(text))
            else:
                processed_input.append(text)

        try:
            response = litellm_module.embedding(
                model = model,
                input = processed_input,
                dimensions = dimensions,
                encoding_format = encoding_format,
                timeout = timeout,
                api_base = api_base,
                api_version = api_version,
                api_key = api_key,
                api_type = api_type,
                caching = caching,
                user = user,
            )
            
            # Convert litellm response to our BasedModel format
            embedding_data = []
            for i, item in enumerate(response.data):
                embedding_data.append(EmbeddingData(
                    embedding=item['embedding'],
                    index=i,
                    object="embedding"
                ))
            
            usage = EmbeddingUsage(
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            return Embedding(
                data=embedding_data,
                model=response.model,
                object="list",
                usage=usage
            )
            
        except Exception as e:
            raise e
    
    @staticmethod
    async def _fastembed_embed(
        model: str,
        input: List[str],
        format: bool = False
    ) -> Embedding:
        """Handle fastembed embedding (async)."""
        if not FASTEMBED_AVAILABLE:
            raise ImportError(
                "fastembed is required for fastembed models. "
                "Install with: pip install fastembed"
            )
        
        # Extract actual model name (remove fastembed/ prefix)
        model_name = model[9:]  # Remove "fastembed/"
        is_sparse = False
        
        # Check if it's a sparse model
        if model_name.startswith("sparse/"):
            is_sparse = True
            model_name = model_name[7:]  # Remove "sparse/"
            fastembed_client = FastSparseTextEmbedding(model_name)
        else:
            fastembed_client = FastTextEmbedding(model_name)
        
        processed_input = []
        for text in input:
            if not isinstance(text, str) and format:
                processed_input.append(convert_to_text(text))
            else:
                processed_input.append(text)
        
        # Generate embeddings
        embeddings = list(fastembed_client.embed(processed_input))
        
        # Convert to our format
        embedding_data = []
        for i, embedding in enumerate(embeddings):
            if is_sparse:
                # For sparse embeddings, convert to dense for compatibility
                # or handle differently based on your needs
                embedding_vector = embedding.values.tolist() if hasattr(embedding, 'values') else list(embedding)
            else:
                embedding_vector = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            embedding_data.append(EmbeddingData(
                embedding=embedding_vector,
                index=i,
                object="embedding"
            ))
        
        # Create usage info (fastembed doesn't provide token counts)
        usage = EmbeddingUsage(
            prompt_tokens=sum(len(text.split()) for text in processed_input),
            total_tokens=sum(len(text.split()) for text in processed_input)
        )
        
        return Embedding(
            data=embedding_data,
            model=model,
            object="list",
            usage=usage
        )
    
    @staticmethod
    def _fastembed_embed_sync(
        model: str,
        input: List[str],
        format: bool = False
    ) -> Embedding:
        """Handle fastembed embedding (sync)."""
        if not FASTEMBED_AVAILABLE:
            raise ImportError(
                "fastembed is required for fastembed models. "
                "Install with: pip install fastembed"
            )
        
        # Extract actual model name (remove fastembed/ prefix)
        model_name = model[9:]  # Remove "fastembed/"
        is_sparse = False
        
        # Check if it's a sparse model
        if model_name.startswith("sparse/"):
            is_sparse = True
            model_name = model_name[7:]  # Remove "sparse/"
            fastembed_client = FastSparseTextEmbedding(model_name)
        else:
            fastembed_client = FastTextEmbedding(model_name)
        
        processed_input = []
        for text in input:
            if not isinstance(text, str) and format:
                processed_input.append(convert_to_text(text))
            else:
                processed_input.append(text)
        
        # Generate embeddings
        embeddings = list(fastembed_client.embed(processed_input))
        
        # Convert to our format
        embedding_data = []
        for i, embedding in enumerate(embeddings):
            if is_sparse:
                # For sparse embeddings, convert to dense for compatibility
                # or handle differently based on your needs
                embedding_vector = embedding.values.tolist() if hasattr(embedding, 'values') else list(embedding)
            else:
                embedding_vector = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            embedding_data.append(EmbeddingData(
                embedding=embedding_vector,
                index=i,
                object="embedding"
            ))
        
        # Create usage info (fastembed doesn't provide token counts)
        usage = EmbeddingUsage(
            prompt_tokens=sum(len(text.split()) for text in processed_input),
            total_tokens=sum(len(text.split()) for text in processed_input)
        )
        
        return Embedding(
            data=embedding_data,
            model=model,
            object="list",
            usage=usage
        )
