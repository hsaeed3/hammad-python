"""hammad.runtime.decorators"""

import functools
from typing import (
    Callable,
    Iterable,
    List,
    Any,
    TypeVar,
    Optional,
    Union,
    cast,
)


__all__ = (
    "sequentialize_function",
    "parallelize_function",
    "update_batch_type_hints",
)


Parameters = TypeVar("Parameters", bound=dict[str, Any])
Return = TypeVar("Return")

TaskParameters = TypeVar("TaskParameters", bound=dict[str, Any])


def sequentialize_function():
    """
    Decorator to make a function that processes a single item (or argument set)
    able to process an iterable of items (or argument sets) sequentially.

    The decorated function will expect an iterable of argument sets as its
    primary argument and will return a list of results. If the underlying
    function raises an error, execution stops and the error propagates.

    Example:
        @sequentialize_function()
        def process_single(data, factor):
            return data * factor

        # Now call it with a list of argument tuples
        results = process_single([(1, 2), (3, 4)])
        # results will be [2, 12]
    """
    from .run import run_sequentially

    def decorator(
        func_to_process_single_item: Callable[..., Return],
    ) -> Callable[[Iterable[TaskParameters]], List[Return]]:
        @functools.wraps(func_to_process_single_item)
        def wrapper(args_list_for_func: Iterable[TaskParameters]) -> List[Return]:
            return run_sequentially(func_to_process_single_item, args_list_for_func)

        return wrapper

    return decorator


def parallelize_function(
    max_workers: Optional[int] = None, timeout: Optional[float] = None
):
    """
    Decorator to make a function that processes a single item (or argument set)
    able to process an iterable of items (or argument sets) in parallel.

    The decorated function will expect an iterable of argument sets as its
    primary argument and will return a list of results or exceptions,
    maintaining the original order.

    Args:
        max_workers (Optional[int]): Max worker threads for parallel execution.
        timeout (Optional[float]): Timeout for each individual task.

    Example:
        @parallelize_function(max_workers=4, timeout=5.0)
        def fetch_url_content(url: str) -> str:
            # ... implementation to fetch url ...
            return "content"

        # Now call it with a list of URLs
        results = fetch_url_content(["http://example.com", "http://example.org"])
        # results will be a list of contents or Exception objects.
    """
    from .run import run_parallel

    def decorator(
        func_to_process_single_item: Callable[..., Return],
    ) -> Callable[[Iterable[TaskParameters]], List[Union[Return, Exception]]]:
        @functools.wraps(func_to_process_single_item)
        def wrapper(
            args_list_for_func: Iterable[TaskParameters],
        ) -> List[Union[Return, Exception]]:
            return run_parallel(
                func_to_process_single_item,
                args_list_for_func,
                max_workers=max_workers,
                timeout=timeout,
            )

        return wrapper

    return decorator


def update_batch_type_hints():
    """
    Decorator that provides better IDE type hinting for functions converted from
    single-item to batch processing. This helps IDEs understand the transformation
    and provide accurate autocomplete and type checking.

    The decorated function maintains proper type information showing it transforms
    from Callable[[T], R] to Callable[[Iterable[T]], List[R]].

    Example:
        @typed_batch()
        def process_url(url: str) -> dict:
            return {"url": url, "status": "ok"}

        # IDE will now correctly understand:
        # process_url: (Iterable[str]) -> List[dict]
        results = process_url(["http://example.com", "http://test.com"])
    """
    from .run import run_sequentially

    def decorator(
        func: Callable[..., Return],
    ) -> Callable[[Iterable[TaskParameters]], List[Return]]:
        @functools.wraps(func)
        def wrapper(args_list: Iterable[TaskParameters]) -> List[Return]:
            return run_sequentially(func, args_list)

        # Preserve original function's type info while updating signature
        wrapper.__annotations__ = {
            "args_list": Iterable[TaskParameters],
            "return": List[Return],
        }

        return cast(Callable[[Iterable[TaskParameters]], List[Return]], wrapper)

    return decorator
