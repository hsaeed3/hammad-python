"""hammad.data.models.pydantic.models.function_model"""

from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, cast
from pydantic import BaseModel
import inspect
from typing import get_type_hints

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

__all__ = ("FunctionModel",)

P = ParamSpec("P")
R = TypeVar("R")


class FunctionModel(BaseModel, Generic[P, R]):
    """
    A specialized pydantic model that acts as a "passthrough" for functions,
    allowing for partial function application.

    ```python
    from cursives.pydantic.models import FunctionModel

    @FunctionModel(exclude = ["y"])
    def some_function(x: int, y: str = "1") -> int:
        return x + len(y)

    print(some_function.call(x=1))
    >>> 2

    print(some_function.function_schema())
    # Create OpenAI compatible function schema easily!
    >>> {
    ...     "name": "some_function",
    ...     "parameters": {
    ...         "x": {"type": "integer"},
    ...         "y": {"type": "string", "default": "1"}
    ...     }
    ... }

    print(some_function.call_from_dict(...))
    """

    def __init__(self, exclude: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self._exclude = exclude or []
        self._original_function: Optional[Callable[P, R]] = None
        self._function_name: Optional[str] = None
        self._signature: Optional[inspect.Signature] = None
        self._type_hints: Optional[Dict[str, Any]] = None

    def __call__(
        self, func: Callable[P, R], exclude: Optional[List[str]] = None
    ) -> "FunctionModel[P, R]":
        """Make this work as a decorator."""
        self._original_function = func
        self._function_name = func.__name__
        self._signature = inspect.signature(func)
        self._type_hints = get_type_hints(func)

        # Create a new instance that wraps the function
        # Use exclude parameter if provided, otherwise use self._exclude
        final_exclude = exclude if exclude is not None else self._exclude
        wrapped: FunctionModel[P, R] = FunctionModel(exclude=final_exclude)
        wrapped._original_function = func
        wrapped._function_name = func.__name__
        wrapped._signature = self._signature
        wrapped._type_hints = self._type_hints

        return wrapped

    def call(self, **kwargs) -> R:
        """Call the wrapped function with provided arguments."""
        if not self._original_function:
            raise ValueError("No function wrapped. Use as decorator first.")

        # Get all parameters from signature
        sig_params = self._signature.parameters
        final_kwargs = {}

        # Add provided kwargs (but not excluded ones)
        for key, value in kwargs.items():
            if key in sig_params and key not in self._exclude:
                final_kwargs[key] = value

        # Add defaults for missing parameters (except excluded ones)
        for param_name, param in sig_params.items():
            if param_name not in final_kwargs and param_name not in self._exclude:
                if param.default is not inspect.Parameter.empty:
                    final_kwargs[param_name] = param.default

        return self._original_function(**final_kwargs)

    def call_from_dict(self, data: Dict[str, Any]) -> R:
        """Call the function using a dictionary of arguments."""
        return self.call(**data)

    def function_schema(self) -> Dict[str, Any]:
        """Generate OpenAI-compatible function schema."""
        if not self._original_function:
            raise ValueError("No function wrapped. Use as decorator first.")

        schema = {
            "name": self._function_name,
            "description": self._original_function.__doc__ or "",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

        # Process each parameter
        for param_name, param in self._signature.parameters.items():
            if param_name in self._exclude:
                continue

            param_type = self._type_hints.get(param_name, Any)

            # Convert Python types to JSON schema types
            json_type = self._python_type_to_json_schema(param_type)

            param_schema = {"type": json_type}

            # Add default if present
            if param.default is not inspect.Parameter.empty:
                param_schema["default"] = param.default
            else:
                schema["parameters"]["required"].append(param_name)

            schema["parameters"]["properties"][param_name] = param_schema

        return schema

    def _python_type_to_json_schema(self, python_type: Any) -> str:
        """Convert Python type to JSON schema type string."""
        if python_type is int:
            return "integer"
        elif python_type is float:
            return "number"
        elif python_type is str:
            return "string"
        elif python_type is bool:
            return "boolean"
        elif python_type is list or python_type is List:
            return "array"
        elif python_type is dict or python_type is Dict:
            return "object"
        else:
            return "string"  # Default fallback

    def partial(self, **kwargs) -> "FunctionModel":
        """Create a new FunctionModel with some arguments pre-filled."""
        if not self._original_function:
            raise ValueError("No function wrapped. Use as decorator first.")

        def partial_func(**additional_kwargs):
            combined_kwargs = {**kwargs, **additional_kwargs}
            return self.call(**combined_kwargs)

        # Create new wrapped function
        new_wrapped = FunctionModel(exclude=self._exclude)
        new_wrapped._original_function = partial_func
        new_wrapped._function_name = f"{self._function_name}_partial"

        # Update signature to remove pre-filled parameters
        new_params = []
        for param_name, param in self._signature.parameters.items():
            if param_name not in kwargs:
                new_params.append(param)

        new_wrapped._signature = inspect.Signature(new_params)
        new_wrapped._type_hints = {
            k: v for k, v in self._type_hints.items() if k not in kwargs
        }

        return new_wrapped
