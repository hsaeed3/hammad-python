"""hammad.service.create

Service creation utilities for launching FastAPI servers from various Python objects.
"""

import inspect
import signal
import atexit
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    Union,
    get_type_hints,
)
from dataclasses import dataclass, fields, is_dataclass, MISSING
from enum import Enum

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, create_model
    from uvicorn import Config, Server
except ImportError as e:
    raise ImportError(
        "Service dependencies not installed. Install with: pip install hammad-python[serve]"
    ) from e

import logging

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enumeration."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceConfig:
    """Configuration for service creation."""

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    reload: bool = False
    workers: int = 1
    timeout_keep_alive: int = 5
    timeout_graceful_shutdown: int = 30
    access_log: bool = True
    use_colors: bool = True
    loop: str = "asyncio"


class ServiceManager:
    """Manages service lifecycle including graceful shutdown."""

    def __init__(self):
        self.servers: List[Server] = []
        self.status = ServiceStatus.STOPPED
        self._shutdown_handlers_registered = False

    def register_shutdown_handlers(self):
        """Register signal handlers for graceful shutdown."""
        if self._shutdown_handlers_registered:
            return

        def signal_handler(signum, _):
            logger.info(f"Received signal {signum}. Shutting down services...")
            self.shutdown_all()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        atexit.register(self.shutdown_all)
        self._shutdown_handlers_registered = True

    def add_server(self, server: Server):
        """Add a server to be managed."""
        self.servers.append(server)
        self.register_shutdown_handlers()

    def shutdown_all(self):
        """Shutdown all managed servers."""
        if self.status == ServiceStatus.STOPPING:
            return

        self.status = ServiceStatus.STOPPING
        logger.info(f"Shutting down {len(self.servers)} service(s)...")

        for server in self.servers:
            try:
                if server.should_exit:
                    continue
                server.should_exit = True
                logger.info("Service shutdown initiated")
            except Exception as e:
                logger.error(f"Error shutting down server: {e}")

        self.status = ServiceStatus.STOPPED
        logger.info("All services shut down")


# Global service manager
_service_manager = ServiceManager()


def _python_type_to_openapi_type(python_type: Type) -> str:
    """Convert Python type to OpenAPI type string."""
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # Handle Union types (Optional)
    if hasattr(python_type, "__origin__"):
        if python_type.__origin__ is Union:
            # For Optional[T], use the non-None type
            non_none_types = [t for t in python_type.__args__ if t != type(None)]
            if non_none_types:
                return _python_type_to_openapi_type(non_none_types[0])
        elif python_type.__origin__ is list:
            return "array"
        elif python_type.__origin__ is dict:
            return "object"

    return type_mapping.get(python_type, "string")


def _create_pydantic_model_from_function(func: Callable) -> Type[BaseModel]:
    """Create a Pydantic model from function signature."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    fields_dict = {}
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        param_type = type_hints.get(param_name, str)
        default_value = (
            ... if param.default == inspect.Parameter.empty else param.default
        )

        fields_dict[param_name] = (param_type, default_value)

    return create_model(f"{func.__name__}Model", **fields_dict)


def _create_fastapi_from_function(
    func: Callable,
    *,
    name: Optional[str] = None,
    method: Literal[
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"
    ] = "POST",
    path: str = "/",
    include_in_schema: bool = True,
    dependencies: Optional[List[Callable[..., Any]]] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> FastAPI:
    """Create a FastAPI app from a function."""
    app_name = name or func.__name__
    app = FastAPI(
        title=app_name,
        description=description or f"Auto-generated API for {func.__name__}",
    )

    # Create request model for POST/PUT/PATCH methods
    if method in ["POST", "PUT", "PATCH"]:
        request_model = _create_pydantic_model_from_function(func)

        async def endpoint(request: request_model):  # type: ignore
            try:
                # Convert request to dict and call function
                kwargs = request.model_dump()
                result = func(**kwargs)
                return {"result": result}
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        app.add_api_route(
            path,
            endpoint,
            methods=[method],
            include_in_schema=include_in_schema,
            dependencies=dependencies,
            tags=tags,
        )
    else:
        # For GET and other methods, use query parameters
        sig = inspect.signature(func)

        async def endpoint(**kwargs):
            try:
                # Filter kwargs to only include function parameters
                func_kwargs = {
                    key: value for key, value in kwargs.items() if key in sig.parameters
                }
                result = func(**func_kwargs)
                return {"result": result}
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Dynamically set the endpoint signature to match the function
        endpoint.__signature__ = sig

        app.add_api_route(
            path,
            endpoint,
            methods=[method],
            include_in_schema=include_in_schema,
            dependencies=dependencies,
            tags=tags,
        )

    return app


def _create_fastapi_from_model(
    model: Union[Type[BaseModel], Type, Any],
    *,
    name: Optional[str] = None,
    methods: List[Literal["GET", "POST", "PUT", "DELETE"]] = None,
    path: str = "/",
    include_in_schema: bool = True,
    dependencies: Optional[List[Callable[..., Any]]] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> FastAPI:
    """Create a FastAPI app from a model (Pydantic, dataclass, etc.)."""
    if methods is None:
        methods = ["GET", "POST"]

    app_name = name or getattr(model, "__name__", "ModelService")
    app = FastAPI(
        title=app_name,
        description=description or f"Auto-generated API for {app_name}",
    )

    # Convert model to Pydantic if needed
    if is_dataclass(model) and not issubclass(model, BaseModel):
        # Convert dataclass to Pydantic model
        field_definitions = {}
        for field in fields(model):
            field_definitions[field.name] = (
                field.type,
                field.default if field.default != MISSING else ...,
            )
        pydantic_model = create_model(f"{model.__name__}Model", **field_definitions)
    elif inspect.isclass(model) and issubclass(model, BaseModel):
        pydantic_model = model
    else:
        # For other types, create a simple wrapper
        pydantic_model = create_model(f"{app_name}Model", value=(str, ...))

    # Store for the service
    items: Dict[str, Any] = {}

    if "GET" in methods:

        @app.get(path, response_model=Dict[str, Any])
        async def get_items():
            return {"items": list(items.values())}

        @app.get(f"{path}/{{item_id}}", response_model=pydantic_model)
        async def get_item(item_id: str):
            if item_id not in items:
                raise HTTPException(status_code=404, detail="Item not found")
            return items[item_id]

    if "POST" in methods:

        @app.post(path, response_model=Dict[str, Any])
        async def create_item(item: pydantic_model):  # type: ignore
            item_id = str(len(items))
            items[item_id] = item
            return {"id": item_id, "item": item}

    if "PUT" in methods:

        @app.put(f"{path}/{{item_id}}", response_model=pydantic_model)
        async def update_item(item_id: str, item: pydantic_model):  # type: ignore
            if item_id not in items:
                raise HTTPException(status_code=404, detail="Item not found")
            items[item_id] = item
            return item

    if "DELETE" in methods:

        @app.delete(f"{path}/{{item_id}}")
        async def delete_item(item_id: str):
            if item_id not in items:
                raise HTTPException(status_code=404, detail="Item not found")
            del items[item_id]
            return {"message": "Item deleted"}

    return app


def create_service(
    target: Union[Callable, Type[BaseModel], Type, Any],
    *,
    # Service configuration
    config: Optional[ServiceConfig] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
    # Function-specific parameters
    name: Optional[str] = None,
    method: Literal[
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"
    ] = "POST",
    path: str = "/",
    # Model-specific parameters
    methods: List[Literal["GET", "POST", "PUT", "DELETE"]] = None,
    # FastAPI parameters
    include_in_schema: bool = True,
    dependencies: Optional[List[Callable[..., Any]]] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
    # Server parameters
    log_level: str = "info",
    reload: bool = False,
    workers: int = 1,
    timeout_keep_alive: int = 5,
    access_log: bool = True,
    use_colors: bool = True,
    auto_start: bool = True,
) -> Union[FastAPI, Server]:
    """
    Create a service from a function, Pydantic model, dataclass, or other object.

    Args:
        target: The function or model to create a service from
        config: ServiceConfig object (overrides individual parameters)
        host: Host to bind to
        port: Port to bind to
        name: Service name (defaults to function/class name)
        method: HTTP method for functions (GET, POST, etc.)
        path: API path
        methods: HTTP methods for models (list of methods)
        include_in_schema: Include in OpenAPI schema
        dependencies: FastAPI dependencies
        tags: API tags
        description: API description
        log_level: Uvicorn log level
        reload: Enable auto-reload
        workers: Number of worker processes
        timeout_keep_alive: Keep-alive timeout
        access_log: Enable access logging
        use_colors: Use colored logs
        auto_start: Automatically start the server

    Returns:
        FastAPI app if auto_start=False, Server instance if auto_start=True
    """
    # Use config if provided, otherwise use individual parameters
    if config:
        host = config.host
        port = config.port
        log_level = config.log_level
        reload = config.reload
        workers = config.workers
        timeout_keep_alive = config.timeout_keep_alive
        access_log = config.access_log
        use_colors = config.use_colors

    # Determine if target is a function or model-like object
    if callable(target) and not inspect.isclass(target):
        # It's a function
        app = _create_fastapi_from_function(
            target,
            name=name,
            method=method,
            path=path,
            include_in_schema=include_in_schema,
            dependencies=dependencies,
            tags=tags,
            description=description,
        )
    else:
        # It's a model-like object (class, Pydantic model, dataclass, etc.)
        app = _create_fastapi_from_model(
            target,
            name=name,
            methods=methods,
            path=path,
            include_in_schema=include_in_schema,
            dependencies=dependencies,
            tags=tags,
            description=description,
        )

    if not auto_start:
        return app

    # Create and configure server
    config_obj = Config(
        app=app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        workers=workers,
        timeout_keep_alive=timeout_keep_alive,
        access_log=access_log,
        use_colors=use_colors,
        loop="asyncio",
    )

    server = Server(config_obj)
    _service_manager.add_server(server)

    logger.info(f"Starting service on {host}:{port}")
    _service_manager.status = ServiceStatus.STARTING

    try:
        server.run()
        _service_manager.status = ServiceStatus.RUNNING
    except Exception as e:
        _service_manager.status = ServiceStatus.ERROR
        logger.error(f"Service failed to start: {e}")
        raise

    return server


async def async_create_service(
    target: Union[Callable, Type[BaseModel], Type, Any],
    *,
    config: Optional[ServiceConfig] = None,
    **kwargs,
) -> Union[FastAPI, Server]:
    """
    Async version of create_service.

    Args:
        target: The function or model to create a service from
        config: ServiceConfig object
        **kwargs: Same as create_service

    Returns:
        FastAPI app if auto_start=False, Server instance if auto_start=True
    """
    # Check if auto_start is provided and respect it
    auto_start = kwargs.get("auto_start", True)

    # Force auto_start=False to get the app first
    kwargs["auto_start"] = False
    app = create_service(target, config=config, **kwargs)

    # If auto_start was False, just return the app
    if not auto_start:
        return app

    # Use config if provided
    if config:
        host = config.host
        port = config.port
        log_level = config.log_level
        reload = config.reload
        workers = config.workers
        timeout_keep_alive = config.timeout_keep_alive
        access_log = config.access_log
        use_colors = config.use_colors
    else:
        host = kwargs.get("host", "0.0.0.0")
        port = kwargs.get("port", 8000)
        log_level = kwargs.get("log_level", "info")
        reload = kwargs.get("reload", False)
        workers = kwargs.get("workers", 1)
        timeout_keep_alive = kwargs.get("timeout_keep_alive", 5)
        access_log = kwargs.get("access_log", True)
        use_colors = kwargs.get("use_colors", True)

    config_obj = Config(
        app=app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        workers=workers,
        timeout_keep_alive=timeout_keep_alive,
        access_log=access_log,
        use_colors=use_colors,
        loop="asyncio",
    )

    server = Server(config_obj)
    _service_manager.add_server(server)

    logger.info(f"Starting async service on {host}:{port}")
    _service_manager.status = ServiceStatus.STARTING

    try:
        await server.serve()
        _service_manager.status = ServiceStatus.RUNNING
    except Exception as e:
        _service_manager.status = ServiceStatus.ERROR
        logger.error(f"Async service failed to start: {e}")
        raise

    return server


def shutdown_all_services():
    """Shutdown all managed services."""
    _service_manager.shutdown_all()


def get_service_status() -> ServiceStatus:
    """Get the current service status."""
    return _service_manager.status
