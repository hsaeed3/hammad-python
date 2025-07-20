"""
Unified Client-Server Architecture for Multi-Protocol Support

This demonstrates a clean foundation where both Client and Server classes
can handle HTTP, OpenAPI, GraphQL, WebSocket, and other protocols through
a simple boolean parameter interface.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List, Callable, Type
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

# Base Protocol Handler Interface
class ProtocolHandler(ABC):
    """Base interface for all protocol handlers"""
    
    @abstractmethod
    async def handle_request(self, request: Any) -> Any:
        """Handle incoming request"""
        pass
    
    @abstractmethod
    async def send_request(self, request: Any) -> Any:
        """Send outgoing request"""
        pass
    
    @abstractmethod
    def get_routes(self) -> Dict[str, Any]:
        """Get protocol-specific routes/endpoints"""
        pass


# HTTP Handler
class HTTPHandler(ProtocolHandler):
    def __init__(self, base_url: Optional[str] = None, **kwargs):
        self.base_url = base_url
        self.session = None  # Would be httpx.AsyncClient
        
    async def handle_request(self, request: Any) -> Any:
        # Server-side HTTP handling
        return {"status": "ok", "protocol": "http"}
    
    async def send_request(self, request: Any) -> Any:
        # Client-side HTTP request
        # Would use httpx here
        return {"response": "http_response"}
    
    def get_routes(self) -> Dict[str, Any]:
        return {
            "/": {"methods": ["GET", "POST"]},
            "/health": {"methods": ["GET"]}
        }


# OpenAPI Handler
class OpenAPIHandler(HTTPHandler):
    def __init__(self, spec: Optional[Union[str, Dict]] = None, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec
        self.operations = {}
        
    async def handle_request(self, request: Any) -> Any:
        # OpenAPI-specific handling
        return {"status": "ok", "protocol": "openapi"}
    
    async def send_request(self, operation_id: str, **kwargs) -> Any:
        # OpenAPI client request
        return {"response": "openapi_response", "operation": operation_id}
    
    def get_routes(self) -> Dict[str, Any]:
        # Parse OpenAPI spec and return routes
        return {
            "/openapi.json": {"methods": ["GET"]},
            "/docs": {"methods": ["GET"]},
            **super().get_routes()
        }


# GraphQL Handler
class GraphQLHandler(ProtocolHandler):
    def __init__(self, schema: Optional[str] = None, **kwargs):
        self.schema = schema
        
    async def handle_request(self, request: Any) -> Any:
        # GraphQL query/mutation handling
        return {"data": {}, "protocol": "graphql"}
    
    async def send_request(self, query: str, variables: Optional[Dict] = None) -> Any:
        # GraphQL client request
        return {"data": {"result": "graphql_response"}}
    
    def get_routes(self) -> Dict[str, Any]:
        return {
            "/graphql": {"methods": ["POST", "GET"]},
            "/graphiql": {"methods": ["GET"]}
        }


# WebSocket Handler
class WebSocketHandler(ProtocolHandler):
    def __init__(self, **kwargs):
        self.connections = set()
        
    async def handle_request(self, request: Any) -> Any:
        # WebSocket connection handling
        return {"status": "connected", "protocol": "websocket"}
    
    async def send_request(self, message: Any) -> Any:
        # WebSocket client message
        return {"response": "ws_response"}
    
    def get_routes(self) -> Dict[str, Any]:
        return {
            "/ws": {"websocket": True}
        }


# gRPC Handler
class GRPCHandler(ProtocolHandler):
    def __init__(self, proto_file: Optional[str] = None, **kwargs):
        self.proto_file = proto_file
        
    async def handle_request(self, request: Any) -> Any:
        return {"status": "ok", "protocol": "grpc"}
    
    async def send_request(self, method: str, request: Any) -> Any:
        return {"response": "grpc_response"}
    
    def get_routes(self) -> Dict[str, Any]:
        return {}  # gRPC doesn't use traditional routes


# Main Server Class
class Server:
    """
    Unified server that can handle multiple protocols based on configuration.
    
    Example:
        server = Server(
            http=True,
            openapi=True,
            graphql=True,
            websocket=True,
            grpc=False
        )
        await server.start()
    """
    
    def __init__(
        self,
        *,
        # Protocol flags
        http: bool = True,
        openapi: bool = False,
        graphql: bool = False,
        websocket: bool = False,
        grpc: bool = False,
        
        # Server configuration
        host: str = "0.0.0.0",
        port: int = 8000,
        
        # Protocol-specific configs
        openapi_spec: Optional[Union[str, Dict]] = None,
        graphql_schema: Optional[str] = None,
        grpc_proto: Optional[str] = None,
        
        # General options
        cors: bool = True,
        auth: Optional[Callable] = None,
        middleware: Optional[List[Callable]] = None,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.handlers: Dict[str, ProtocolHandler] = {}
        
        # Initialize protocol handlers based on flags
        if http and not openapi:  # OpenAPI extends HTTP
            self.handlers["http"] = HTTPHandler(**kwargs)
            
        if openapi:
            self.handlers["openapi"] = OpenAPIHandler(spec=openapi_spec, **kwargs)
            
        if graphql:
            self.handlers["graphql"] = GraphQLHandler(schema=graphql_schema, **kwargs)
            
        if websocket:
            self.handlers["websocket"] = WebSocketHandler(**kwargs)
            
        if grpc:
            self.handlers["grpc"] = GRPCHandler(proto_file=grpc_proto, **kwargs)
            
        # Store middleware and auth
        self.auth = auth
        self.middleware = middleware or []
        self.cors = cors
        
        # Will hold the actual server instance (FastAPI, etc.)
        self._app = None
        self._server = None
        
    def _build_app(self):
        """Build the underlying application based on enabled protocols"""
        # In practice, this would create a FastAPI app and configure it
        # based on the enabled handlers
        
        routes = {}
        for name, handler in self.handlers.items():
            routes.update(handler.get_routes())
            
        # Would actually create and configure FastAPI here
        return {"type": "fastapi", "routes": routes}
    
    async def start(self):
        """Start the server with all configured protocols"""
        self._app = self._build_app()
        
        logging.info(f"Starting server on {self.host}:{self.port}")
        logging.info(f"Enabled protocols: {list(self.handlers.keys())}")
        
        # In practice, would start uvicorn here
        await asyncio.sleep(0.1)  # Simulate startup
        
        return self
        
    async def stop(self):
        """Stop the server gracefully"""
        logging.info("Stopping server...")
        # Cleanup code here
        

# Main Client Class  
class Client:
    """
    Unified client that can communicate with multiple protocols.
    
    Example:
        client = Client(
            base_url="http://localhost:8000",
            http=True,
            openapi=True,
            graphql=True,
            websocket=True
        )
        
        # HTTP request
        response = await client.http.get("/users")
        
        # OpenAPI request
        response = await client.openapi.execute("getUser", user_id=123)
        
        # GraphQL request
        response = await client.graphql.query("{ users { id name } }")
    """
    
    def __init__(
        self,
        base_url: str,
        *,
        # Protocol flags
        http: bool = True,
        openapi: bool = False,
        graphql: bool = False,
        websocket: bool = False,
        grpc: bool = False,
        
        # Authentication
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        basic_auth: Optional[tuple[str, str]] = None,
        
        # Protocol-specific configs
        openapi_spec: Optional[Union[str, Dict]] = None,
        graphql_schema: Optional[str] = None,
        grpc_proto: Optional[str] = None,
        
        # Client options
        timeout: float = 30.0,
        verify_ssl: bool = True,
        **kwargs
    ):
        self.base_url = base_url
        self.handlers: Dict[str, ProtocolHandler] = {}
        
        # Store auth config
        self.auth_config = {
            "api_key": api_key,
            "bearer_token": bearer_token,
            "basic_auth": basic_auth
        }
        
        # Initialize handlers
        if http and not openapi:
            self.handlers["http"] = HTTPHandler(base_url=base_url, **kwargs)
            
        if openapi:
            self.handlers["openapi"] = OpenAPIHandler(
                base_url=base_url,
                spec=openapi_spec,
                **kwargs
            )
            
        if graphql:
            self.handlers["graphql"] = GraphQLHandler(
                schema=graphql_schema,
                **kwargs
            )
            
        if websocket:
            self.handlers["websocket"] = WebSocketHandler(**kwargs)
            
        if grpc:
            self.handlers["grpc"] = GRPCHandler(proto_file=grpc_proto, **kwargs)
            
        # Create convenient accessors
        self._create_protocol_accessors()
        
    def _create_protocol_accessors(self):
        """Create convenient accessor properties for each protocol"""
        for name, handler in self.handlers.items():
            setattr(self, name, ProtocolAccessor(handler, self.auth_config))
            
    async def close(self):
        """Close all client connections"""
        # Cleanup code here
        pass


# Protocol Accessor for clean API
class ProtocolAccessor:
    """Provides clean API access to protocol handlers"""
    
    def __init__(self, handler: ProtocolHandler, auth_config: Dict[str, Any]):
        self.handler = handler
        self.auth_config = auth_config
        
    async def request(self, *args, **kwargs):
        """Generic request method"""
        return await self.handler.send_request(*args, **kwargs)
        
    # Protocol-specific convenience methods would be added here
    async def get(self, path: str, **kwargs):
        """HTTP GET request"""
        if isinstance(self.handler, HTTPHandler):
            return await self.handler.send_request({"method": "GET", "path": path, **kwargs})
        raise NotImplementedError(f"GET not supported for {type(self.handler).__name__}")
        
    async def post(self, path: str, data: Any = None, **kwargs):
        """HTTP POST request"""
        if isinstance(self.handler, HTTPHandler):
            return await self.handler.send_request({"method": "POST", "path": path, "data": data, **kwargs})
        raise NotImplementedError(f"POST not supported for {type(self.handler).__name__}")
        
    async def execute(self, operation_id: str, **kwargs):
        """Execute OpenAPI operation"""
        if isinstance(self.handler, OpenAPIHandler):
            return await self.handler.send_request(operation_id, **kwargs)
        raise NotImplementedError(f"execute not supported for {type(self.handler).__name__}")
        
    async def query(self, query: str, variables: Optional[Dict] = None):
        """Execute GraphQL query"""
        if isinstance(self.handler, GraphQLHandler):
            return await self.handler.send_request(query, variables)
        raise NotImplementedError(f"query not supported for {type(self.handler).__name__}")


# Example usage functions
async def example_server():
    """Example of creating and running a multi-protocol server"""
    
    # Create a server that handles HTTP, OpenAPI, and GraphQL
    server = Server(
        http=True,
        openapi=True,
        graphql=True,
        websocket=True,
        
        # OpenAPI spec could be a file path or dict
        openapi_spec="./api-spec.yaml",
        
        # GraphQL schema
        graphql_schema="""
        type Query {
            users: [User]
            user(id: ID!): User
        }
        
        type User {
            id: ID!
            name: String!
            email: String!
        }
        """,
        
        # Server config
        host="0.0.0.0",
        port=8000,
        cors=True
    )
    
    # Start the server
    await server.start()
    
    # Server is now running and handling multiple protocols
    # - HTTP endpoints at /
    # - OpenAPI at /docs and /openapi.json
    # - GraphQL at /graphql and /graphiql
    # - WebSocket at /ws
    
    return server


async def example_client():
    """Example of using the unified client"""
    
    # Create a client that can speak multiple protocols
    client = Client(
        base_url="http://localhost:8000",
        http=True,
        openapi=True,
        graphql=True,
        websocket=True,
        
        # Authentication
        bearer_token="my-api-token",
        
        # Load OpenAPI spec from server
        openapi_spec="http://localhost:8000/openapi.json"
    )
    
    # Use HTTP
    users = await client.http.get("/users")
    user = await client.http.post("/users", data={"name": "John", "email": "john@example.com"})
    
    # Use OpenAPI (with auto-discovered operations)
    user = await client.openapi.execute("getUser", user_id=123)
    users = await client.openapi.execute("listUsers", limit=10)
    
    # Use GraphQL
    result = await client.graphql.query("""
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                name
                email
            }
        }
    """, variables={"id": "123"})
    
    # WebSocket (would implement actual WebSocket client)
    # await client.websocket.connect()
    # await client.websocket.send({"type": "message", "data": "Hello"})
    
    # Cleanup
    await client.close()
    
    return client


# Helper function to create paired client-server
def create_service_pair(
    *,
    protocols: List[str] = ["http", "openapi"],
    server_config: Optional[Dict] = None,
    client_config: Optional[Dict] = None
) -> tuple[Server, Client]:
    """
    Create a paired Server and Client with matching protocol support.
    
    Example:
        server, client = create_service_pair(
            protocols=["http", "openapi", "graphql"],
            server_config={"port": 8080},
            client_config={"timeout": 60.0}
        )
    """
    server_config = server_config or {}
    client_config = client_config or {}
    
    # Set protocol flags
    protocol_flags = {p: p in protocols for p in ["http", "openapi", "graphql", "websocket", "grpc"]}
    
    # Create server
    server = Server(**protocol_flags, **server_config)
    
    # Create client with matching protocols
    base_url = f"http://{server.host}:{server.port}"
    client = Client(base_url=base_url, **protocol_flags, **client_config)
    
    return server, client


# Main entry point for testing
async def main():
    """Test the architecture"""
    
    # Example 1: Simple HTTP service
    print("=== Simple HTTP Service ===")
    server, client = create_service_pair(protocols=["http"])
    await server.start()
    
    # Example 2: Full-featured API service
    print("\n=== Multi-Protocol Service ===")
    api_server = Server(
        http=True,
        openapi=True,
        graphql=True,
        websocket=True,
        port=8080
    )
    await api_server.start()
    
    # Example 3: Client-only usage
    print("\n=== Client Usage ===")
    client = Client(
        base_url="https://api.example.com",
        http=True,
        openapi=True,
        bearer_token="secret-token"
    )
    
    print("Architecture demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())