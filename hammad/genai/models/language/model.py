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
import functools
import inspect
import asyncio
from typing_extensions import Literal

if TYPE_CHECKING:
    from httpx import Timeout

from ....logging.logger import _get_internal_logger
from ..model_provider import litellm, instructor

from ...types.base import BaseGenAIModel
from .types.language_model_instructor_mode import LanguageModelInstructorMode
from .types.language_model_name import LanguageModelName
from .types.language_model_messages import LanguageModelMessages
from .types.language_model_response import LanguageModelResponse
from .types.language_model_settings import LanguageModelSettings
from .types.language_model_stream import LanguageModelStream

from .utils import (
    parse_messages_input,
    handle_completion_request_params,
    handle_completion_response,
    handle_structured_output_request_params,
    prepare_response_model,
    handle_structured_output_response,
    format_tool_calls,
    LanguageModelRequestBuilder,
)

__all__ = [
    "LanguageModel",
    "LanguageModelError",
    "create_language_model",
]

T = TypeVar("T")


logger = _get_internal_logger(__name__)


class LanguageModelError(Exception):
    """Error raised when an error occurs during a language model operation."""

    def __init__(self, message: str, *args: Any, **kwargs: Any):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.args = args
        self.kwargs = kwargs


class LanguageModel(BaseGenAIModel, Generic[T]):
    """
    A Generative AI model that can be used to generate text, chat completions,
    structured outputs, call tools and more.
    """

    model: LanguageModelName | str = "openai/gpt-4o-mini"
    """The model to use for requests."""

    type: Type[T] = str
    """The type of the output of the language model."""

    instructions: Optional[str] = None
    """Instructions for the language model."""

    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    deployment_id: Optional[str] = None
    model_list: Optional[List[Any]] = None
    extra_headers: Optional[Dict[str, str]] = None

    settings: LanguageModelSettings = LanguageModelSettings()
    """Settings for the language model."""

    instructor_mode: LanguageModelInstructorMode = "tool_call"
    """Default instructor mode for structured outputs."""

    def __init__(
        self,
        model: LanguageModelName = "openai/gpt-4o-mini",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instructor_mode: LanguageModelInstructorMode = "tool_call",
        verbose: bool = False,
        debug: bool = False,
        **kwargs: Any,
    ):
        """Initialize the language model.

        Args:
            model: The model to use for requests
            base_url: Custom base URL for the API
            api_key: API key for authentication
            instructor_mode: Default instructor mode for structured outputs
            verbose: If True, set logger to INFO level for detailed output
            debug: If True, set logger to DEBUG level for maximum verbosity
            **kwargs: Additional arguments passed to BaseGenAIModel
        """
        # Initialize BaseGenAIModel via super()
        super().__init__(model=model, base_url=base_url, api_key=api_key, **kwargs)

        # Initialize LanguageModel-specific attributes
        self._instructor_client = None
        self.verbose = verbose
        self.debug = debug

        # Set logger level based on verbose/debug flags
        if debug:
            logger.setLevel("DEBUG")
        elif verbose:
            logger.setLevel("INFO")

        logger.info(f"Initialized LanguageModel w/ model: {self.model}")
        logger.debug(f"LanguageModel settings: {self.settings}")

    def _get_instructor_client(
        self, mode: Optional[LanguageModelInstructorMode] = None
    ):
        """Get or create an instructor client with the specified mode."""
        effective_mode = mode or self.instructor_mode

        # Create a new client if mode changed or client doesn't exist
        if (
            self._instructor_client is None
            or getattr(self._instructor_client, "_mode", None) != effective_mode
        ):
            logger.debug(
                f"Creating new instructor client for mode: {effective_mode} from old mode: {getattr(self._instructor_client, '_mode', None)}"
            )

            self._instructor_client = instructor.from_litellm(
                completion=litellm.completion, mode=instructor.Mode(effective_mode)
            )
            self._instructor_client._mode = effective_mode

        return self._instructor_client

    def _get_async_instructor_client(
        self, mode: Optional[LanguageModelInstructorMode] = None
    ):
        """Get or create an async instructor client with the specified mode."""
        effective_mode = mode or self.instructor_mode

        return instructor.from_litellm(
            completion=litellm.acompletion, mode=instructor.Mode(effective_mode)
        )

    # Overloaded run methods for different return types

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[str]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[str]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[T]: ...

    @overload
    def run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[T]: ...

    def run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        mock_response: Optional[str] = None,
        verbose: Optional[bool] = None,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Union[LanguageModelResponse[Any], LanguageModelStream[Any]]:
        """Run a language model request.

        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            mock_response: Mock response string for testing (saves API costs)
            verbose: If True, set logger to INFO level for this request
            debug: If True, set logger to DEBUG level for this request
            **kwargs: Additional request parameters

        Returns:
            LanguageModelResponse or LanguageModelStream depending on parameters
        """
        # Set logger level for this request if specified
        original_level = logger.level
        if debug or (debug is None and self.debug):
            logger.setLevel("DEBUG")
        elif verbose or (verbose is None and self.verbose):
            logger.setLevel("INFO")

        logger.info(f"Running LanguageModel request with model: {self.model}")
        logger.debug(f"LanguageModel request kwargs: {kwargs}")

        try:
            # Extract model, base_url, api_key, and mock_response from kwargs, using instance defaults
            model = kwargs.pop("model", None) or self.model
            base_url = kwargs.pop("base_url", None) or self.base_url
            api_key = kwargs.pop("api_key", None) or self.api_key
            mock_response_param = kwargs.pop("mock_response", None) or mock_response

            # Add base_url, api_key, and mock_response to kwargs if they are set
            if base_url is not None:
                kwargs["base_url"] = base_url
            if api_key is not None:
                kwargs["api_key"] = api_key
            if mock_response_param is not None:
                kwargs["mock_response"] = mock_response_param

            # Create the request
            request = LanguageModelRequestBuilder(
                messages=messages, instructions=instructions, model=model, **kwargs
            )

            # Parse messages
            parsed_messages = parse_messages_input(
                request.messages, request.instructions
            )
            if request.is_structured_output():
                parsed_messages = format_tool_calls(parsed_messages)

            # Handle different request types
            if request.is_structured_output():
                return self._handle_structured_output_request(request, parsed_messages)
            else:
                return self._handle_completion_request(request, parsed_messages)

        except Exception as e:
            raise LanguageModelError(f"Error in language model request: {e}") from e
        finally:
            # Restore original logger level
            if debug is not None or verbose is not None:
                logger.setLevel(original_level)

    # Overloaded async_run methods for different return types

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[str]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[str]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[str]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[False] = False,
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelResponse[T]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        *,
        type: Type[T],
        stream: Literal[True],
        model: Optional[LanguageModelName | str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[T]: ...

    @overload
    async def async_run(
        self,
        messages: LanguageModelMessages,
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
        mock_response: Optional[str] = None,
        **kwargs: Any,
    ) -> LanguageModelStream[T]: ...

    async def async_run(
        self,
        messages: LanguageModelMessages,
        instructions: Optional[str] = None,
        mock_response: Optional[str] = None,
        verbose: Optional[bool] = None,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Union[LanguageModelResponse[Any], LanguageModelStream[Any]]:
        """Run an async language model request.

        Args:
            messages: The input messages/content for the request
            instructions: Optional system instructions to prepend
            mock_response: Mock response string for testing (saves API costs)
            verbose: If True, set logger to INFO level for this request
            debug: If True, set logger to DEBUG level for this request
            **kwargs: Additional request parameters

        Returns:
            LanguageModelResponse or LanguageModelAsyncStream depending on parameters
        """
        # Set logger level for this request if specified
        original_level = logger.level
        if debug or (debug is None and self.debug):
            logger.setLevel("DEBUG")
        elif verbose or (verbose is None and self.verbose):
            logger.setLevel("INFO")

        logger.info(f"Running async LanguageModel request with model: {self.model}")
        logger.debug(f"LanguageModel request kwargs: {kwargs}")

        try:
            # Extract model, base_url, api_key, and mock_response from kwargs, using instance defaults
            model = kwargs.pop("model", None) or self.model
            base_url = kwargs.pop("base_url", None) or self.base_url
            api_key = kwargs.pop("api_key", None) or self.api_key
            mock_response_param = kwargs.pop("mock_response", None) or mock_response

            # Add base_url, api_key, and mock_response to kwargs if they are set
            if base_url is not None:
                kwargs["base_url"] = base_url
            if api_key is not None:
                kwargs["api_key"] = api_key
            if mock_response_param is not None:
                kwargs["mock_response"] = mock_response_param

            # Create the request
            request = LanguageModelRequestBuilder(
                messages=messages, instructions=instructions, model=model, **kwargs
            )

            # Parse messages
            parsed_messages = parse_messages_input(
                request.messages, request.instructions
            )
            if request.is_structured_output():
                parsed_messages = format_tool_calls(parsed_messages)

            # Handle different request types
            if request.is_structured_output():
                return await self._handle_async_structured_output_request(
                    request, parsed_messages
                )
            else:
                return await self._handle_async_completion_request(
                    request, parsed_messages
                )

        except Exception as e:
            raise LanguageModelError(
                f"Error in async language model request: {e}"
            ) from e
        finally:
            # Restore original logger level
            if debug is not None or verbose is not None:
                logger.setLevel(original_level)

    def _handle_completion_request(
        self, request: LanguageModelRequestBuilder, parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[str], LanguageModelStream[str]]:
        """Handle a standard completion request."""
        # Get filtered parameters
        params = handle_completion_request_params(request.get_completion_settings())
        params["messages"] = parsed_messages

        if request.is_streaming():
            # Handle streaming - stream parameter is already in params
            if "stream_options" not in params and "stream_options" in request.settings:
                params["stream_options"] = request.settings["stream_options"]
            stream = litellm.completion(**params)
            return LanguageModelStream(
                model=request.model,
                stream=stream,
                output_type=str,
            )
        else:
            # Handle non-streaming
            response = litellm.completion(**params)
            return handle_completion_response(response, request.model)

    async def _handle_async_completion_request(
        self, request: LanguageModelRequestBuilder, parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[str], LanguageModelStream[str]]:
        """Handle an async standard completion request."""
        # Get filtered parameters
        params = handle_completion_request_params(request.get_completion_settings())
        params["messages"] = parsed_messages

        if request.is_streaming():
            # Handle streaming - stream parameter is already in params
            if "stream_options" not in params and "stream_options" in request.settings:
                params["stream_options"] = request.settings["stream_options"]
            stream = await litellm.acompletion(**params)
            return LanguageModelStream(
                model=request.model,
                stream=stream,
                output_type=str,
            )
        else:
            # Handle non-streaming
            response = await litellm.acompletion(**params)
            return handle_completion_response(response, request.model)

    def _handle_structured_output_request(
        self, request: LanguageModelRequestBuilder, parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[Any], LanguageModelStream[Any]]:
        """Handle a structured output request."""
        # Get filtered parameters
        params = handle_structured_output_request_params(
            request.get_structured_output_settings()
        )
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
            return LanguageModelStream(
                model=request.model,
                stream=stream,
                output_type=request.get_output_type(),
                response_field_name=request.get_response_field_name(),
            )
        else:
            # Handle non-streaming
            response, completion = client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=request.get_max_retries(),
                strict=request.get_strict_mode(),
                **params,
            )
            return handle_structured_output_response(
                response,
                completion,
                request.model,
                request.get_output_type(),
                request.get_response_field_name(),
            )

    async def _handle_async_structured_output_request(
        self, request: LanguageModelRequestBuilder, parsed_messages: List[Any]
    ) -> Union[LanguageModelResponse[Any], LanguageModelStream[Any]]:
        """Handle an async structured output request."""
        # Get filtered parameters
        params = handle_structured_output_request_params(
            request.get_structured_output_settings()
        )
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
            return LanguageModelStream(
                model=request.model,
                stream=stream,
                output_type=request.get_output_type(),
                response_field_name=request.get_response_field_name(),
            )
        else:
            # Handle non-streaming
            response, completion = await client.chat.completions.create_with_completion(
                response_model=response_model,
                max_retries=request.get_max_retries(),
                strict=request.get_strict_mode(),
                **params,
            )
            return handle_structured_output_response(
                response,
                completion,
                request.model,
                request.get_output_type(),
                request.get_response_field_name(),
            )

    def as_tool(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Callable, Any]:
        """Convert this language model to a tool that can be used by agents.

        Can be used as a decorator or as a function:

        As a decorator:
        @model.as_tool()
        def my_function(param1: str, param2: int) -> MyType:
            '''Function description'''
            pass

        As a function:
        tool = model.as_tool(
            name="my_tool",
            description="Tool description",
            instructions="Custom instructions for the LLM"
        )

        Args:
            func: The function to wrap (when used as decorator)
            name: The name of the tool
            description: Description of what the tool does
            instructions: Custom instructions for the LLM generation
            **kwargs: Additional arguments for tool creation

        Returns:
            BaseTool or decorated function
        """
        from ...types.base import BaseTool
        from ....formatting.text.converters import convert_docstring_to_text

        def create_tool_wrapper(target_func: Optional[Callable] = None) -> Any:
            """Create a tool wrapper for the language model."""

            if target_func is not None:
                # Decorator usage - use function signature and docstring
                sig = inspect.signature(target_func)
                func_name = name or target_func.__name__

                # Get return type from function signature
                return_type = (
                    sig.return_annotation
                    if sig.return_annotation != inspect.Signature.empty
                    else str
                )

                # Extract docstring as system instructions
                system_instructions = instructions or convert_docstring_to_text(
                    target_func
                )

                # Create parameter schema from function signature
                parameters_schema = {"type": "object", "properties": {}, "required": []}

                for param_name, param in sig.parameters.items():
                    param_type = (
                        param.annotation
                        if param.annotation != inspect.Parameter.empty
                        else str
                    )

                    # Convert type to JSON schema type
                    if param_type == str:
                        json_type = "string"
                    elif param_type == int:
                        json_type = "integer"
                    elif param_type == float:
                        json_type = "number"
                    elif param_type == bool:
                        json_type = "boolean"
                    elif param_type == list:
                        json_type = "array"
                    elif param_type == dict:
                        json_type = "object"
                    else:
                        json_type = "string"  # Default fallback

                    parameters_schema["properties"][param_name] = {
                        "type": json_type,
                        "description": f"Parameter {param_name} of type {param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)}",
                    }

                    if param.default == inspect.Parameter.empty:
                        parameters_schema["required"].append(param_name)

                # Create partial function with model settings
                partial_func = functools.partial(
                    self._execute_tool_function,
                    target_func=target_func,
                    return_type=return_type,
                    system_instructions=system_instructions,
                )

                # Handle async functions
                if asyncio.iscoroutinefunction(target_func):

                    async def async_tool_function(**tool_kwargs: Any) -> Any:
                        return await partial_func(**tool_kwargs)

                    return BaseTool(
                        name=func_name,
                        description=description
                        or system_instructions
                        or f"Tool for {func_name}",
                        function=async_tool_function,
                        parameters_json_schema=parameters_schema,
                        **kwargs,
                    )
                else:

                    def sync_tool_function(**tool_kwargs: Any) -> Any:
                        return partial_func(**tool_kwargs)

                    return BaseTool(
                        name=func_name,
                        description=description
                        or system_instructions
                        or f"Tool for {func_name}",
                        function=sync_tool_function,
                        parameters_json_schema=parameters_schema,
                        **kwargs,
                    )
            else:
                # Function usage - create generic tool
                tool_name = name or f"language_model_{self.model.replace('/', '_')}"
                tool_description = (
                    description or f"Language model tool using {self.model}"
                )

                # Create partial function with model settings
                partial_func = functools.partial(
                    self._execute_generic_tool, system_instructions=instructions
                )

                def generic_tool_function(
                    input: str, type: Optional[Type[T]] = None, **tool_kwargs: Any
                ) -> Any:
                    """Generic tool function that runs the language model."""
                    return partial_func(input=input, output_type=type, **tool_kwargs)

                # Generic parameter schema
                parameters_schema = {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "The input text for the language model",
                        },
                        "type": {
                            "type": "string",
                            "description": "Optional output type specification",
                        },
                    },
                    "required": ["input"],
                }

                return BaseTool(
                    name=tool_name,
                    description=tool_description,
                    function=generic_tool_function,
                    parameters_json_schema=parameters_schema,
                    **kwargs,
                )

        if func is None:
            # Called as @model.as_tool() or model.as_tool()
            return create_tool_wrapper
        else:
            # Called as @model.as_tool (without parentheses)
            return create_tool_wrapper(func)

    def _execute_tool_function(
        self,
        target_func: Callable,
        return_type: Type,
        system_instructions: str,
        **kwargs: Any,
    ) -> Any:
        """Execute a function-based tool using the language model."""
        # Format the function call parameters
        param_text = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        input_text = f"Function: {target_func.__name__}({param_text})"

        # Use the language model to generate structured output
        if return_type != str:
            response = self.run(
                messages=[{"role": "user", "content": input_text}],
                instructions=system_instructions,
                type=return_type,
            )
        else:
            response = self.run(
                messages=[{"role": "user", "content": input_text}],
                instructions=system_instructions,
            )

        return response.output

    def _execute_generic_tool(
        self,
        input: str,
        output_type: Optional[Type] = None,
        system_instructions: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a generic tool using the language model."""
        if output_type and output_type != str:
            response = self.run(
                messages=[{"role": "user", "content": input}],
                instructions=system_instructions,
                type=output_type,
                **kwargs,
            )
        else:
            response = self.run(
                messages=[{"role": "user", "content": input}],
                instructions=system_instructions,
                **kwargs,
            )

        return response.output


def create_language_model(
    model: str | LanguageModelName = "openai/gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    organization: Optional[str] = None,
    deployment_id: Optional[str] = None,
    model_list: Optional[List[Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    verbose: bool = False,
    debug: bool = False,
) -> LanguageModel:
    """Create a language model instance."""
    return LanguageModel(
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_version=api_version,
        organization=organization,
        deployment_id=deployment_id,
        model_list=model_list,
        extra_headers=extra_headers,
        verbose=verbose,
        debug=debug,
    )
