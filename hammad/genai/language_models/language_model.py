"""hammad.genai.language_models.language_model"""

from typing import (
    Any, 
    Callable,
    List, 
    TypeVar, 
    Generic, 
    Union, 
    Optional, 
    Type, 
    overload, 
    Dict, 
    TYPE_CHECKING,
)
from typing_extensions import Literal

if TYPE_CHECKING:
    from httpx import Timeout

from ._types import LanguageModelName, LanguageModelInstructorMode
from ._utils import (
    parse_messages_input,
    handle_completion_request_params,
    handle_completion_response,
    handle_structured_output_request_params,
    prepare_response_model,
    handle_structured_output_response,
    format_tool_calls,
    LanguageModelRequestBuilder,
)
from .language_model_request import LanguageModelRequest, LanguageModelMessagesParam
from .language_model_response import LanguageModelResponse
from ._streaming import Stream, AsyncStream

__all__ = [
    "LanguageModel",
    "LanguageModelError",
]

T = TypeVar("T")


class LanguageModelError(Exception):
    """Error raised when an error occurs during a language model operation."""
    
    def __init__(self, message: str, *args: Any, **kwargs: Any):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.args = args
        self.kwargs = kwargs


class _AIProvider:
    """Provider for accessing litellm and instructor instances."""
    
    _LITELLM = None
    _INSTRUCTOR = None
    
    @staticmethod
    def get_litellm():
        """Returns the `litellm` module."""
        if _AIProvider._LITELLM is None:
            try:
                import litellm
                litellm.drop_params = True
                litellm.modify_params = True
                _AIProvider._LITELLM = litellm
                
                # Rebuild LanguageModelResponse model now that litellm is available
                LanguageModelResponse.model_rebuild()
            except ImportError as e:
                raise ImportError(
                    "Using the `hammad.ai.llms` extension requires the `litellm` package to be installed.\n"
                    "Please either install the `litellm` package, or install the `hammad.ai` extension with:\n"
                    "`pip install 'hammad-python[ai]'`"
                ) from e
        return _AIProvider._LITELLM
    
    @staticmethod
    def get_instructor():
        """Returns the `instructor` module."""
        if _AIProvider._INSTRUCTOR is None:
            try:
                import instructor
                _AIProvider._INSTRUCTOR = instructor
            except ImportError as e:
                raise ImportError(
                    "Using the `hammad.ai.llms` extension requires the `instructor` package to be installed.\n"
                    "Please either install the `instructor` package, or install the `hammad.ai` extension with:\n"
                    "`pip install 'hammad-python[ai]'`"
                ) from e
        return _AIProvider._INSTRUCTOR


class LanguageModel(Generic[T]):
    """A clean language model interface for generating responses with comprehensive
    parameter handling and type safety."""
    
    def __init__(
        self,
        model: LanguageModelName = "openai/gpt-4o-mini",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instructor_mode: LanguageModelInstructorMode = "tool_call",
    ):
        """Initialize the language model.
        
        Args:
            model: The model to use for requests
            instructor_mode: Default instructor mode for structured outputs
        """
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.instructor_mode = instructor_mode
        self._instructor_client = None
    
    def _get_instructor_client(self, mode: Optional[LanguageModelInstructorMode] = None):
        """Get or create an instructor client with the specified mode."""
        effective_mode = mode or self.instructor_mode
        
        # Create a new client if mode changed or client doesn't exist
        if (self._instructor_client is None or 
            getattr(self._instructor_client, '_mode', None) != effective_mode):
            
            instructor = _AIProvider.get_instructor()
            self._instructor_client = instructor.from_litellm(
                completion=_AIProvider.get_litellm().completion,
                mode=instructor.Mode(effective_mode)
            )
            self._instructor_client._mode = effective_mode
            
        return self._instructor_client
    
    def _get_async_instructor_client(self, mode: Optional[LanguageModelInstructorMode] = None):
        """Get or create an async instructor client with the specified mode."""
        effective_mode = mode or self.instructor_mode
        
        instructor = _AIProvider.get_instructor()
        return instructor.from_litellm(
            completion=_AIProvider.get_litellm().acompletion,
            mode=instructor.Mode(effective_mode)
        )
    
    # Overloaded run methods for different return types
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Any]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Stream[str]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Any]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> Stream[str]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        response_field_name: Optional[str] = None,
        response_field_instruction: Optional[str] = None,
        response_model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        strict: Optional[bool] = None,
        validation_context: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
        completion_response_hooks: Optional[List[Callable[..., None]]] = None,
        completion_error_hooks: Optional[List[Callable[..., None]]] = None,
        completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
        parse_error_hooks: Optional[List[Callable[..., None]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Stream[T]: ...
    
    @overload
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        response_field_name: Optional[str] = None,
        response_field_instruction: Optional[str] = None,
        response_model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        strict: Optional[bool] = None,
        validation_context: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
        completion_response_hooks: Optional[List[Callable[..., None]]] = None,
        completion_error_hooks: Optional[List[Callable[..., None]]] = None,
        completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
        parse_error_hooks: Optional[List[Callable[..., None]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> Stream[T]: ...
    
    def run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[LanguageModelResponse[Any], Stream[Any]]:
        """Run a language model request.
        
        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            **kwargs: Additional request parameters
            
        Returns:
            LanguageModelResponse or LanguageModelStream depending on parameters
        """
        try:
            # Extract model, base_url, and api_key from kwargs, using instance defaults
            model = kwargs.pop("model", None) or self.model
            base_url = kwargs.pop("base_url", None) or self.base_url
            api_key = kwargs.pop("api_key", None) or self.api_key
            
            # Add base_url and api_key to kwargs if they are set
            if base_url is not None:
                kwargs["base_url"] = base_url
            if api_key is not None:
                kwargs["api_key"] = api_key
            
            # Create the request
            request = LanguageModelRequestBuilder(
                messages=messages,
                instructions=instructions,
                model=model,
                **kwargs
            )
            
            # Parse messages
            parsed_messages = parse_messages_input(request.messages, request.instructions)
            parsed_messages = format_tool_calls(parsed_messages)
            
            # Handle different request types
            if request.is_structured_output():
                return self._handle_structured_output_request(request, parsed_messages)
            else:
                return self._handle_completion_request(request, parsed_messages)
                
        except Exception as e:
            raise LanguageModelError(f"Error in language model request: {e}") from e
    
    # Overloaded async_run methods for different return types
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Any]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncStream[str]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Any]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncStream[str]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        response_field_name: Optional[str] = None,
        response_field_instruction: Optional[str] = None,
        response_model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        strict: Optional[bool] = None,
        validation_context: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
        completion_response_hooks: Optional[List[Callable[..., None]]] = None,
        completion_error_hooks: Optional[List[Callable[..., None]]] = None,
        completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
        parse_error_hooks: Optional[List[Callable[..., None]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncStream[T]: ...
    
    @overload
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        instructor_mode: Optional[LanguageModelInstructorMode] = None,
        response_field_name: Optional[str] = None,
        response_field_instruction: Optional[str] = None,
        response_model_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        strict: Optional[bool] = None,
        validation_context: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        completion_kwargs_hooks: Optional[List[Callable[..., None]]] = None,
        completion_response_hooks: Optional[List[Callable[..., None]]] = None,
        completion_error_hooks: Optional[List[Callable[..., None]]] = None,
        completion_last_attempt_hooks: Optional[List[Callable[..., None]]] = None,
        parse_error_hooks: Optional[List[Callable[..., None]]] = None,
        timeout: Optional[Union[float, str, "Timeout"]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncStream[T]: ...
    
    async def async_run(
        self,
        messages: LanguageModelMessagesParam,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[LanguageModelResponse[Any], AsyncStream[Any]]:
        """Run an async language model request.
        
        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            **kwargs: Additional request parameters
            
        Returns:
            LanguageModelResponse or LanguageModelAsyncStream depending on parameters
        """
        try:
            # Extract model, base_url, and api_key from kwargs, using instance defaults
            model = kwargs.pop("model", None) or self.model
            base_url = kwargs.pop("base_url", None) or self.base_url
            api_key = kwargs.pop("api_key", None) or self.api_key
            
            # Add base_url and api_key to kwargs if they are set
            if base_url is not None:
                kwargs["base_url"] = base_url
            if api_key is not None:
                kwargs["api_key"] = api_key
            
            # Create the request
            request = LanguageModelRequestBuilder(
                messages=messages,
                instructions=instructions,
                model=model,
                **kwargs
            )
            
            # Parse messages
            parsed_messages = parse_messages_input(request.messages, request.instructions)
            parsed_messages = format_tool_calls(parsed_messages)
            
            # Handle different request types
            if request.is_structured_output():
                return await self._handle_async_structured_output_request(request, parsed_messages)
            else:
                return await self._handle_async_completion_request(request, parsed_messages)
                
        except Exception as e:
            raise LanguageModelError(f"Error in async language model request: {e}") from e
    
    def _handle_completion_request(
        self, 
        request: LanguageModelRequestBuilder, 
        parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[str], Stream[str]]:
        """Handle a standard completion request."""
        # Get filtered parameters
        params = handle_completion_request_params(request.get_completion_settings())
        params["messages"] = parsed_messages
        
        litellm = _AIProvider.get_litellm()
        
        if request.is_streaming():
            # Handle streaming - stream parameter is already in params
            if "stream_options" not in params and "stream_options" in request.settings:
                params["stream_options"] = request.settings["stream_options"]
            stream = litellm.completion(**params)
            return Stream(stream, output_type=str, model=request.model)
        else:
            # Handle non-streaming
            response = litellm.completion(**params)
            return handle_completion_response(response, request.model)
    
    async def _handle_async_completion_request(
        self, 
        request: LanguageModelRequestBuilder, 
        parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[str], AsyncStream[str]]:
        """Handle an async standard completion request."""
        # Get filtered parameters
        params = handle_completion_request_params(request.get_completion_settings())
        params["messages"] = parsed_messages
        
        litellm = _AIProvider.get_litellm()
        
        if request.is_streaming():
            # Handle streaming - stream parameter is already in params
            if "stream_options" not in params and "stream_options" in request.settings:
                params["stream_options"] = request.settings["stream_options"]
            stream = await litellm.acompletion(**params)
            return AsyncStream(stream, output_type=str, model=request.model)
        else:
            # Handle non-streaming
            response = await litellm.acompletion(**params)
            return handle_completion_response(response, request.model)
    
    def _handle_structured_output_request(
        self, 
        request: LanguageModelRequestBuilder, 
        parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[Any], Stream[Any]]:
        """Handle a structured output request."""
        # Get filtered parameters
        params = handle_structured_output_request_params(request.get_structured_output_settings())
        params["messages"] = parsed_messages
        
        # Prepare response model
        response_model = prepare_response_model(
            request.get_output_type(),
            request.get_response_field_name(),
            request.get_response_field_instruction(),
            request.get_response_model_name(),
        )
        
        # Get instructor client
        client = self._get_instructor_client(request.get_instructor_mode())
        
        if request.is_streaming():
            if isinstance(request.get_output_type(), list):
                # Handle streaming - stream parameter is already in params
                stream = client.chat.completions.create_iterable(
                    response_model=response_model,
                    max_retries=request.get_max_retries(),
                    strict=request.get_strict_mode(),
                    **params,
                )
            else:
                # Handle streaming - stream parameter is already in params
                stream = client.chat.completions.create_partial(
                    response_model=response_model,
                    max_retries=request.get_max_retries(),
                    strict=request.get_strict_mode(),
                    **params,
                )
            return Stream(stream, output_type=request.get_output_type(), model=request.model, response_field_name=request.get_response_field_name())
        else:
            # Handle non-streaming
            response, completion = client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=request.get_max_retries(),
                strict=request.get_strict_mode(),
                **params,
            )
            return handle_structured_output_response(
                response, completion, request.model, request.get_output_type(), request.get_response_field_name()
            )
    
    async def _handle_async_structured_output_request(
        self, 
        request: LanguageModelRequestBuilder, 
        parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[Any], AsyncStream[Any]]:
        """Handle an async structured output request."""
        # Get filtered parameters
        params = handle_structured_output_request_params(request.get_structured_output_settings())
        params["messages"] = parsed_messages
        
        # Prepare response model
        response_model = prepare_response_model(
            request.get_output_type(),
            request.get_response_field_name(),
            request.get_response_field_instruction(),
            request.get_response_model_name(),
        )
        
        # Get async instructor client
        client = self._get_async_instructor_client(request.get_instructor_mode())
        
        if request.is_streaming():
            if isinstance(request.get_output_type(), list):
                # Handle streaming - stream parameter is already in params
                stream = client.chat.completions.create_iterable(
                    response_model=response_model,
                    max_retries=request.get_max_retries(),
                    strict=request.get_strict_mode(),
                    **params,
                )
            else:
                # Handle streaming - stream parameter is already in params
                stream = client.chat.completions.create_partial(
                    response_model=response_model,
                    max_retries=request.get_max_retries(),
                    strict=request.get_strict_mode(),
                    **params,
                )
            return AsyncStream(stream, output_type=request.get_output_type(), model=request.model, response_field_name=request.get_response_field_name())
        else:
            # Handle non-streaming
            response, completion = await client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=request.get_max_retries(),
                strict=request.get_strict_mode(),
                **params,
            )
            return handle_structured_output_response(
                response, completion, request.model, request.get_output_type(), request.get_response_field_name()
            )