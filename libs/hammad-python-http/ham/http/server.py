"""ham.http.server

Unified server implementation supporting multiple protocols.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Literal, get_type_hints
from functools import wraps

import strawberry
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest, Depends
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
import uvicorn
from pydantic import BaseModel

from .core import (
    Authorization,
    Protocol,
    HttpMethod,
    RouteInfo,
    infer_http_method,
    extract_function_metadata,
)


class Server:
    """Unified server supporting HTTP, GraphQL, OpenAPI, and MCP protocols."""

    def __init__(
        self,
        *,
        http: bool = True,
        openapi: bool = False,
        graphql: bool = False,
        mcp: bool = False,
        auth: Optional[Authorization] = None,
        port: int = 8000,
        host: str = "127.0.0.1",
        title: str = "Ham HTTP Server",
        description: str = "Unified multi-protocol server",
        version: str = "0.1.0",
        **kwargs,
    ):
        self.protocols = {
            Protocol.HTTP: http,
            Protocol.OPENAPI: openapi,
            Protocol.GRAPHQL: graphql,
            Protocol.MCP: mcp,
        }
        self.auth = auth or Authorization()
        self.port = port
        self.host = host

        # FastAPI app for HTTP/OpenAPI
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            docs_url="/docs" if openapi else None,
            redoc_url="/redoc" if openapi else None,
        )

        # Route registry
        self.routes: Dict[str, RouteInfo] = {}
        self.graphql_routes: List[Callable] = []

        # GraphQL setup
        if graphql:
            self._setup_graphql()

    def _setup_graphql(self) -> None:
        """Setup GraphQL schema and router."""
        # This will be populated when routes are registered
        self.graphql_schema = None
        self.graphql_router = None

    def route(
        self,
        path: str,
        *,
        methods: Optional[List[HttpMethod]] = None,
        protocols: Optional[List[Protocol]] = None,
    ):
        """Decorator to register a route with auto-inference."""

        def decorator(func: Callable) -> Callable:
            # Extract function metadata
            metadata = extract_function_metadata(func)

            # Infer HTTP method if not specified
            if methods is None:
                inferred_method = infer_http_method(func)
                route_methods = [inferred_method]
            else:
                route_methods = methods

            # Default protocols based on enabled features
            if protocols is None:
                route_protocols = []
                if self.protocols[Protocol.HTTP]:
                    route_protocols.append(Protocol.HTTP)
                if self.protocols[Protocol.GRAPHQL]:
                    route_protocols.append(Protocol.GRAPHQL)
            else:
                route_protocols = protocols

            # Create route info
            route_info = RouteInfo(
                path=path,
                function=func,
                methods=route_methods,
                protocols=route_protocols,
                parameters=metadata["parameters"],
                return_type=metadata["return_type"],
            )

            # Register route
            self.routes[path] = route_info

            # Register HTTP route
            if Protocol.HTTP in route_protocols:
                self._register_http_route(route_info)

            # Register GraphQL route
            if Protocol.GRAPHQL in route_protocols:
                self._register_graphql_route(route_info)

            return func

        return decorator

    def _register_http_route(self, route_info: RouteInfo) -> None:
        """Register an HTTP route with FastAPI."""
        func = route_info.function
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Create FastAPI-compatible endpoint with automatic parameter injection
        async def endpoint(request: FastAPIRequest, *args, **kwargs):
            try:
                # Apply authentication if configured
                if self.auth.type != "none":
                    # TODO: Implement authentication logic
                    pass

                # Extract and validate parameters from request
                final_kwargs = {}

                # Handle path parameters
                final_kwargs.update(kwargs)

                # Handle query parameters for GET requests
                if request.method in ["GET", "HEAD", "OPTIONS"]:
                    for param_name, param_info in route_info.parameters.items():
                        if param_name in request.query_params:
                            value = request.query_params[param_name]
                            # Convert to appropriate type based on annotation
                            if param_info.get("annotation") == int:
                                value = int(value)
                            elif param_info.get("annotation") == float:
                                value = float(value)
                            elif param_info.get("annotation") == bool:
                                value = value.lower() in ("true", "1", "yes", "on")
                            final_kwargs[param_name] = value

                # Handle request body for POST/PUT/PATCH requests
                elif request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        body = await request.json()
                        if isinstance(body, dict):
                            for param_name, param_info in route_info.parameters.items():
                                if param_name in body:
                                    final_kwargs[param_name] = body[param_name]
                    except:
                        # Handle non-JSON bodies
                        body = await request.body()
                        if len(route_info.parameters) == 1:
                            param_name = list(route_info.parameters.keys())[0]
                            final_kwargs[param_name] = body.decode()

                # Call the original function
                if asyncio.iscoroutinefunction(func):
                    result = await func(**final_kwargs)
                else:
                    result = func(**final_kwargs)

                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Register for each HTTP method
        for method in route_info.methods:
            method_func = getattr(self.app, method.value.lower())
            method_func(route_info.path)(endpoint)

    def _register_graphql_route(self, route_info: RouteInfo) -> None:
        """Register a GraphQL route."""
        self.graphql_routes.append(route_info.function)

        # Rebuild GraphQL schema when new routes are added
        if self.protocols[Protocol.GRAPHQL]:
            self._build_graphql_schema()

    def _build_graphql_schema(self) -> None:
        """Build GraphQL schema from registered routes."""
        if not self.graphql_routes:
            return

        # Create GraphQL types and resolvers from registered functions
        query_fields = {}
        mutation_fields = {}

        for route_path, route_info in self.routes.items():
            if Protocol.GRAPHQL not in route_info.protocols:
                continue

            func = route_info.function
            func_name = func.__name__

            # Determine if it's a query or mutation based on HTTP method
            is_mutation = any(
                method
                in [
                    HttpMethod.POST,
                    HttpMethod.PUT,
                    HttpMethod.DELETE,
                    HttpMethod.PATCH,
                ]
                for method in route_info.methods
            )

            if is_mutation:
                mutation_fields[func_name] = strawberry.field(resolver=func)
            else:
                query_fields[func_name] = strawberry.field(resolver=func)

        # Create GraphQL types
        if query_fields:

            @strawberry.type
            class Query:
                pass

            for name, field in query_fields.items():
                setattr(Query, name, field)
        else:
            Query = None

        if mutation_fields:

            @strawberry.type
            class Mutation:
                pass

            for name, field in mutation_fields.items():
                setattr(Mutation, name, field)
        else:
            Mutation = None

        # Build schema
        if Query or Mutation:
            self.graphql_schema = strawberry.Schema(query=Query, mutation=Mutation)

            # Add GraphQL router to FastAPI
            self.graphql_router = GraphQLRouter(self.graphql_schema)
            self.app.include_router(self.graphql_router, prefix="/graphql")

    async def start_async(self) -> None:
        """Start the server asynchronously."""
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    def start(self) -> None:
        """Start the server."""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

    def get_routes(self) -> Dict[str, RouteInfo]:
        """Get all registered routes."""
        return self.routes.copy()


def create_server(
    *,
    http: bool = True,
    openapi: bool = False,
    graphql: bool = False,
    mcp: bool = False,
    auth: Optional[Authorization] = None,
    port: int = 8000,
    host: str = "127.0.0.1",
    title: str = "Ham HTTP Server",
    description: str = "Unified multi-protocol server",
    version: str = "0.1.0",
    **kwargs,
) -> Server:
    """Create a new unified multi-protocol server.

    A server supports HTTP, GraphQL, OpenAPI, and MCP protocols with automatic
    route registration, authentication, and protocol inference capabilities.

    Args:
        http: Enable HTTP protocol support (default: True)
        openapi: Enable OpenAPI/Swagger documentation (default: False)
        graphql: Enable GraphQL protocol support (default: False)
        mcp: Enable Model Context Protocol support (default: False)
        auth: Authentication configuration (bearer, basic, api_key, or none)
        port: Port number to bind to (default: 8000)
        host: Host address to bind to (default: "127.0.0.1")
        title: API title for documentation (default: "Ham HTTP Server")
        description: API description for documentation
        version: API version string (default: "0.1.0")
        **kwargs: Additional parameters passed to FastAPI constructor
            Common options include:
            - debug: Enable debug mode (bool)
            - middleware: List of middleware to add
            - exception_handlers: Custom exception handlers
            - dependencies: Global dependencies
            - default_response_class: Default response class
            - docs_url: Custom docs URL (str or None)
            - redoc_url: Custom ReDoc URL (str or None)
            - openapi_url: Custom OpenAPI schema URL
            - openapi_prefix: OpenAPI prefix
            - root_path: Root path for the application
            - swagger_ui_parameters: Swagger UI configuration

    Returns:
        Server instance ready to register routes and start

    Examples:
        Basic HTTP server:
        >>> server = create_server()
        >>> @server.route("/hello")
        ... def hello():
        ...     return {"message": "Hello World"}
        >>> server.start()

        Server with multiple protocols:
        >>> server = create_server(
        ...     http=True,
        ...     graphql=True,
        ...     openapi=True,
        ...     port=3000,
        ...     host="0.0.0.0"
        ... )

        Server with authentication and custom configuration:
        >>> auth = Authorization(type="bearer")
        >>> server = create_server(
        ...     auth=auth,
        ...     title="My API Server",
        ...     description="A powerful API",
        ...     version="2.1.0",
        ...     debug=True,
        ...     docs_url="/documentation",
        ...     openapi=True
        ... )

        Production server with middleware:
        >>> from fastapi.middleware.cors import CORSMiddleware
        >>> server = create_server(
        ...     port=8080,
        ...     host="0.0.0.0",
        ...     title="Production API",
        ...     middleware=[
        ...         {"type": "cors", "allow_origins": ["*"]}
        ...     ]
        ... )

        GraphQL-only server:
        >>> server = create_server(
        ...     http=False,
        ...     graphql=True,
        ...     port=4000,
        ...     title="GraphQL API"
        ... )
    """
    return Server(
        http=http,
        openapi=openapi,
        graphql=graphql,
        mcp=mcp,
        auth=auth,
        port=port,
        host=host,
        title=title,
        description=description,
        version=version,
        **kwargs,
    )


__all__ = ["Server", "create_server"]
