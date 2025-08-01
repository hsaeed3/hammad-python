"""hammad.genai.a2a.workers"""

from typing import Union, Optional, Any, Dict, List, TYPE_CHECKING
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import uuid

from fasta2a import FastA2A, Worker
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage
from fasta2a.schema import Artifact, Message, TaskIdParams, TaskSendParams, TextPart

if TYPE_CHECKING:
    from ..agents.agent import Agent
    from ..graphs.base import BaseGraph

__all__ = [
    "as_a2a_app",
    "GraphWorker",
    "AgentWorker",
]


Context = List[Message]
"""The shape of the context stored in the storage."""


class GraphWorker(Worker[Context]):
    """Worker implementation for BaseGraph instances."""

    def __init__(
        self,
        graph: "BaseGraph",
        storage: InMemoryStorage,
        broker: InMemoryBroker,
        state: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize the GraphWorker.

        Args:
            graph: The BaseGraph instance to run
            storage: Storage backend for tasks and context
            broker: Broker for task scheduling
            state: Optional initial state for the graph
            **kwargs: Additional arguments passed to Worker
        """
        super().__init__(storage=storage, broker=broker, **kwargs)
        self.graph = graph
        self.state = state

    async def run_task(self, params: TaskSendParams) -> None:
        """Execute a task using the graph."""
        task = await self.storage.load_task(params["id"])
        assert task is not None

        await self.storage.update_task(task["id"], state="working")

        # Load context
        context = await self.storage.load_context(task["context_id"]) or []
        context.extend(task.get("history", []))

        # Build message history for the graph
        history = self.build_message_history(context)

        # Extract the user's message from the task
        user_message = ""
        for msg in task.get("history", []):
            if msg.get("role") == "user":
                # Get the text content from the message parts
                for part in msg.get("parts", []):
                    if part.get("kind") == "text":
                        user_message = part.get("text", "")
                        break
                if user_message:
                    break

        try:
            # Run the graph with the user message and history
            result = await self.graph.async_run(
                user_message, state=self.state, history=history
            )

            # Create response message
            message = Message(
                role="assistant",
                parts=[TextPart(text=str(result.output), kind="text")],
                kind="message",
                message_id=str(uuid.uuid4()),
            )

            # Update context with new message
            context.append(message)

            # Build artifacts from the result
            artifacts = self.build_artifacts(result)

            # Update storage
            await self.storage.update_context(task["context_id"], context)
            await self.storage.update_task(
                task["id"],
                state="completed",
                new_messages=[message],
                new_artifacts=artifacts,
            )

        except Exception as e:
            # Handle errors
            error_message = Message(
                role="assistant",
                parts=[TextPart(text=f"Error: {str(e)}", kind="text")],
                kind="message",
                message_id=str(uuid.uuid4()),
            )

            context.append(error_message)
            await self.storage.update_context(task["context_id"], context)
            await self.storage.update_task(
                task["id"],
                state="failed",
                new_messages=[error_message],
                new_artifacts=[],
            )

    async def cancel_task(self, params: TaskIdParams) -> None:
        """Cancel a running task."""
        # For now, just mark the task as cancelled
        await self.storage.update_task(params["id"], state="cancelled")

    def build_message_history(self, history: List[Message]) -> List[Dict[str, Any]]:
        """Convert A2A messages to graph message format."""
        messages = []
        for msg in history:
            role = msg.get("role", "user")
            content = ""

            # Extract text content from message parts
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    content = part.get("text", "")
                    break

            if content:
                messages.append({"role": role, "content": content})

        return messages

    def build_artifacts(self, result: Any) -> List[Artifact]:
        """Build artifacts from graph execution result."""
        artifacts = []

        # Add the main output as an artifact
        if hasattr(result, "output"):
            artifacts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "data": str(result.output),
                    "metadata": {
                        "source": "graph_output",
                        "model": getattr(result, "model", "unknown"),
                    },
                }
            )

        # Add state as an artifact if available
        if hasattr(result, "state") and result.state is not None:
            artifacts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "state",
                    "data": str(result.state),
                    "metadata": {"source": "graph_state"},
                }
            )

        # Add execution metadata
        if hasattr(result, "nodes_executed"):
            artifacts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "metadata",
                    "data": {
                        "nodes_executed": result.nodes_executed,
                        "start_node": getattr(result, "start_node", None),
                    },
                    "metadata": {"source": "graph_execution"},
                }
            )

        return artifacts


class AgentWorker(Worker[Context]):
    """Worker implementation for Agent instances."""

    def __init__(
        self,
        agent: "Agent",
        storage: InMemoryStorage,
        broker: InMemoryBroker,
        context: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize the AgentWorker.

        Args:
            agent: The Agent instance to run
            storage: Storage backend for tasks and context
            broker: Broker for task scheduling
            context: Optional initial context for the agent
            **kwargs: Additional arguments passed to Worker
        """
        super().__init__(storage=storage, broker=broker, **kwargs)
        self.agent = agent
        self.agent_context = context

    async def run_task(self, params: TaskSendParams) -> None:
        """Execute a task using the agent."""
        task = await self.storage.load_task(params["id"])
        assert task is not None

        await self.storage.update_task(task["id"], state="working")

        # Load context
        context = await self.storage.load_context(task["context_id"]) or []
        context.extend(task.get("history", []))

        # Build message history for the agent
        history = self.build_message_history(context)

        # Extract the user's message from the task
        user_message = ""
        for msg in task.get("history", []):
            if msg.get("role") == "user":
                # Get the text content from the message parts
                for part in msg.get("parts", []):
                    if part.get("kind") == "text":
                        user_message = part.get("text", "")
                        break
                if user_message:
                    break

        try:
            # Prepare messages for the agent
            messages = history if history else []
            if user_message:
                messages.append({"role": "user", "content": user_message})

            # Run the agent
            result = await self.agent.async_run(
                messages=messages, context=self.agent_context
            )

            # Create response message
            message = Message(
                role="assistant",
                parts=[TextPart(text=str(result.output), kind="text")],
                kind="message",
                message_id=str(uuid.uuid4()),
            )

            # Update context with new message
            context.append(message)

            # Build artifacts from the result
            artifacts = self.build_artifacts(result)

            # Update the agent context if it was modified
            if hasattr(result, "context") and result.context is not None:
                self.agent_context = result.context

            # Update storage
            await self.storage.update_context(task["context_id"], context)
            await self.storage.update_task(
                task["id"],
                state="completed",
                new_messages=[message],
                new_artifacts=artifacts,
            )

        except Exception as e:
            # Handle errors
            error_message = Message(
                role="assistant",
                parts=[TextPart(text=f"Error: {str(e)}", kind="text")],
                kind="message",
                message_id=str(uuid.uuid4()),
            )

            context.append(error_message)
            await self.storage.update_context(task["context_id"], context)
            await self.storage.update_task(
                task["id"],
                state="failed",
                new_messages=[error_message],
                new_artifacts=[],
            )

    async def cancel_task(self, params: TaskIdParams) -> None:
        """Cancel a running task."""
        # For now, just mark the task as cancelled
        await self.storage.update_task(params["id"], state="cancelled")

    def build_message_history(self, history: List[Message]) -> List[Dict[str, Any]]:
        """Convert A2A messages to agent message format."""
        messages = []
        for msg in history:
            role = msg.get("role", "user")
            content = ""

            # Extract text content from message parts
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    content = part.get("text", "")
                    break

            if content:
                messages.append({"role": role, "content": content})

        return messages

    def build_artifacts(self, result: Any) -> List[Artifact]:
        """Build artifacts from agent execution result."""
        artifacts = []

        # Add the main output as an artifact
        if hasattr(result, "output"):
            artifacts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "data": str(result.output),
                    "metadata": {
                        "source": "agent_output",
                        "model": getattr(result, "model", self.agent.model),
                    },
                }
            )

        # Add context as an artifact if available
        if hasattr(result, "context") and result.context is not None:
            artifacts.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "context",
                    "data": str(result.context),
                    "metadata": {"source": "agent_context"},
                }
            )

        # Add steps/tool calls as artifacts
        if hasattr(result, "steps") and result.steps:
            for i, step in enumerate(result.steps):
                if hasattr(step, "tool_calls") and step.tool_calls:
                    for tool_call in step.tool_calls:
                        artifacts.append(
                            {
                                "id": str(uuid.uuid4()),
                                "type": "tool_call",
                                "data": {
                                    "tool": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                    "step": i + 1,
                                },
                                "metadata": {"source": "agent_tool_call"},
                            }
                        )

        return artifacts


def as_a2a_app(
    instance: Union["Agent", "BaseGraph"],
    *,
    # Worker configuration
    state: Optional[Any] = None,
    context: Optional[Any] = None,
    # Storage and broker configuration
    storage: Optional[Any] = None,
    broker: Optional[Any] = None,
    # Server configuration
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    log_level: str = "info",
    # A2A configuration
    name: Optional[str] = None,
    url: Optional[str] = None,
    version: str = "1.0.0",
    description: Optional[str] = None,
    # Advanced configuration
    lifespan_timeout: int = 30,
    **uvicorn_kwargs: Any,
) -> FastA2A:
    """
    Launch an Agent or BaseGraph as an A2A server.

    This function creates a fully parameterized A2A server that can handle
    requests for either Agent or BaseGraph instances. It sets up the necessary
    Worker, Storage, and Broker components automatically.

    Args:
        instance: Either an Agent or BaseGraph instance to serve
        state: Initial state for graphs (ignored for agents)
        context: Initial context for agents (ignored for graphs)
        storage: Custom storage backend (defaults to InMemoryStorage)
        broker: Custom broker backend (defaults to InMemoryBroker)
        host: Host to bind the server to
        port: Port to bind the server to
        reload: Enable auto-reload for development
        workers: Number of worker processes
        log_level: Logging level
        name: Agent name for the A2A server
        url: URL where the agent is hosted
        version: API version
        description: API description for the A2A server
        lifespan_timeout: Timeout for lifespan events
        **uvicorn_kwargs: Additional arguments passed to uvicorn

    Returns:
        FastA2A application instance

    Examples:
        Launch an agent as A2A server:
        ```python
        from hammad import Agent

        agent = Agent(
            name="assistant",
            instructions="You are a helpful assistant",
            model="openai/gpt-4"
        )

        app = as_a2a_app(agent, port=8080)
        # Run with: uvicorn module:app
        ```

        Launch a graph as A2A server:
        ```python
        from hammad import BaseGraph, action

        class MyGraph(BaseGraph):
            @action.start()
            def process(self, message: str) -> str:
                return f"Processed: {message}"

        graph = MyGraph()
        app = as_a2a_app(graph, name="My Graph API")
        # Run with: uvicorn module:app
        ```

        Run directly with uvicorn:
        ```python
        import uvicorn

        app = as_a2a_app(agent)
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```
    """
    # Import here to avoid circular imports
    from ..agents.agent import Agent
    from ..graphs.base import BaseGraph

    # Create storage and broker if not provided
    if storage is None:
        storage = InMemoryStorage()
    if broker is None:
        broker = InMemoryBroker()

    # Determine instance type and create appropriate worker
    if isinstance(instance, Agent):
        worker = AgentWorker(
            agent=instance, storage=storage, broker=broker, context=context
        )
        default_name = instance.name
        default_description = (
            instance.description or f"A2A server for {instance.name} agent"
        )
    elif isinstance(instance, BaseGraph):
        worker = GraphWorker(
            graph=instance, storage=storage, broker=broker, state=state
        )
        default_name = instance.__class__.__name__
        default_description = (
            instance.__class__.__doc__
            or f"A2A server for {instance.__class__.__name__} graph"
        )
    else:
        raise ValueError(
            f"Instance must be either an Agent or BaseGraph, got {type(instance)}"
        )

    # Use provided values or defaults
    agent_name = name or default_name
    agent_url = url or f"http://{host}:{port}"
    agent_description = description or default_description

    # Create lifespan context manager
    @asynccontextmanager
    async def lifespan(app: FastA2A) -> AsyncIterator[None]:
        """Lifespan context manager for the A2A server."""
        # Start the task manager
        async with app.task_manager:
            # Start the worker
            async with worker.run():
                yield

    # Create the FastA2A application with correct parameters
    app = FastA2A(
        storage=storage,
        broker=broker,
        lifespan=lifespan,
        name=agent_name,
        url=agent_url,
        version=version,
        description=agent_description,
    )

    # Store configuration for potential runtime access
    app.state.instance = instance
    app.state.worker = worker
    app.state.host = host
    app.state.port = port
    app.state.reload = reload
    app.state.workers = workers
    app.state.log_level = log_level
    app.state.uvicorn_kwargs = uvicorn_kwargs

    # Add a helper method to run the server directly
    def run_server():
        """Run the A2A server using uvicorn."""
        import uvicorn

        uvicorn_config = {
            "host": host,
            "port": port,
            "reload": reload,
            "workers": workers
            if not reload
            else 1,  # Can't use multiple workers with reload
            "log_level": log_level,
            **uvicorn_kwargs,
        }

        uvicorn.run(app, **uvicorn_config)

    # Attach the run method to the app for convenience
    app.run_server = run_server

    return app
