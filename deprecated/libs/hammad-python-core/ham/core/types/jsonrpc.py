"""ham.core.types.jsonrpc

JSONRPC bindings for Python (Ported from `Anthropic's` `mcp` bindings)
"""

from collections.abc import Callable
from typing import Annotated, Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict, Field, RootModel

ProgressToken = str | int
Cursor = str
Role = Literal["user", "assistant"]
RequestId = Annotated[int | str, Field(union_mode="left_to_right")]
AnyFunction: TypeAlias = Callable[..., Any]


class RequestParams(BaseModel):
    class Meta(BaseModel):
        progressToken: ProgressToken | None = None
        """
        If specified, the caller requests out-of-band progress notifications for
        this request (as represented by notifications/progress). The value of this
        parameter is an opaque token that will be attached to any subsequent
        notifications. The receiver is not obligated to provide these notifications.
        """

        model_config = ConfigDict(extra="allow")

    meta: Meta | None = Field(alias="_meta", default=None)


class PaginatedRequestParams(RequestParams):
    cursor: Cursor | None = None
    """
    An opaque token representing the current pagination position.
    If provided, the server should return results starting after this cursor.
    """


class NotificationParams(BaseModel):
    class Meta(BaseModel):
        model_config = ConfigDict(extra="allow")

    meta: Meta | None = Field(alias="_meta", default=None)
    """
    See [MCP specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/47339c03c143bb4ec01a26e721a1b8fe66634ebe/docs/specification/draft/basic/index.mdx#general-fields)
    for notes on _meta usage.
    """


RequestParamsT = TypeVar("RequestParamsT", bound=RequestParams | dict[str, Any] | None)
NotificationParamsT = TypeVar(
    "NotificationParamsT", bound=NotificationParams | dict[str, Any] | None
)
MethodT = TypeVar("MethodT", bound=str)


class Request(BaseModel, Generic[RequestParamsT, MethodT]):
    """Base class for JSON-RPC requests."""

    method: MethodT
    params: RequestParamsT
    model_config = ConfigDict(extra="allow")


class PaginatedRequest(
    Request[PaginatedRequestParams | None, MethodT], Generic[MethodT]
):
    """Base class for paginated requests,
    matching the schema's PaginatedRequest interface."""

    params: PaginatedRequestParams | None = None


class Notification(BaseModel, Generic[NotificationParamsT, MethodT]):
    """Base class for JSON-RPC notifications."""

    method: MethodT
    params: NotificationParamsT
    model_config = ConfigDict(extra="allow")


class Result(BaseModel):
    """Base class for JSON-RPC results."""

    meta: dict[str, Any] | None = Field(alias="_meta", default=None)
    """
    See [MCP specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/47339c03c143bb4ec01a26e721a1b8fe66634ebe/docs/specification/draft/basic/index.mdx#general-fields)
    for notes on _meta usage.
    """
    model_config = ConfigDict(extra="allow")


class PaginatedResult(Result):
    nextCursor: Cursor | None = None
    """
    An opaque token representing the pagination position after the last returned result.
    If present, there may be more results available.
    """


class JSONRPCRequest(Request[dict[str, Any] | None, str]):
    """A request that expects a response."""

    jsonrpc: Literal["2.0"]
    id: RequestId
    method: str
    params: dict[str, Any] | None = None


class JSONRPCNotification(Notification[dict[str, Any] | None, str]):
    """A notification which does not expect a response."""

    jsonrpc: Literal["2.0"]
    params: dict[str, Any] | None = None


class JSONRPCResponse(BaseModel):
    """A successful (non-error) response to a request."""

    jsonrpc: Literal["2.0"]
    id: RequestId
    result: dict[str, Any]
    model_config = ConfigDict(extra="allow")


# SDK error codes
CONNECTION_CLOSED = -32000
# REQUEST_TIMEOUT = -32001  # the typescript sdk uses this

# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class ErrorData(BaseModel):
    """Error information for JSON-RPC error responses."""

    code: int
    """The error type that occurred."""

    message: str
    """
    A short description of the error. The message SHOULD be limited to a concise single
    sentence.
    """

    data: Any | None = None
    """
    Additional information about the error. The value of this member is defined by the
    sender (e.g. detailed error information, nested errors etc.).
    """

    model_config = ConfigDict(extra="allow")


class JSONRPCError(BaseModel):
    """A response to a request that indicates an error occurred."""

    jsonrpc: Literal["2.0"]
    id: str | int
    error: ErrorData
    model_config = ConfigDict(extra="allow")


class JSONRPCMessage(
    RootModel[JSONRPCRequest | JSONRPCNotification | JSONRPCResponse | JSONRPCError]
):
    pass


__all__ = (
    "JSONRPCRequest",
    "JSONRPCNotification",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCMessage",
)
