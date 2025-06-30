"""hammad.multithreading"""

import concurrent.futures
import functools
import time
from typing import (
    Callable,
    Iterable,
    List,
    Any,
    TypeVar,
    Tuple,
    Optional,
    Union,
    Type,
    cast,
    overload,
)
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    retry_if_exception_message,
    retry_if_exception_type,
)

T_Arg = TypeVar("T_Arg")
R_Out = TypeVar("R_Out")

SingleTaskArgs = Union[T_Arg, Tuple[Any, ...]]


__all__ = (
    "run_sequentially",
    "run_parallel",
    "sequentialize",
    "parallelize",
    "typed_batch",
    "run_with_retry",
    "retry",
    "wait_exponential",
    "stop_after_attempt",
    "retry_if_exception_type",
    "retry_if_exception_message",
    "retry_if_exception_type",
)


def run_sequentially(
    func: Callable[..., R_Out], args_list: Iterable[SingleTaskArgs]
) -> List[R_Out]:
    """
    Executes a function sequentially for each set of arguments in args_list.
    If the function raises an exception during any call, the execution stops
    and the exception is propagated.

    Args:
        func: The function to execute.
        args_list: An iterable of arguments (or argument tuples) to pass to func.
                   - If func takes multiple arguments (e.g., func(a, b)),
                     each item in args_list should be a tuple (e.g., [(val1_a, val1_b), (val2_a, val2_b)]).
                   - If func takes one argument (e.g., func(a)),
                     each item can be the argument itself (e.g., [val1, val2]).
                   - If func takes no arguments (e.g., func()),
                     each item should be an empty tuple (e.g., [(), ()]).

    Returns:
        A list of results from the sequential execution.
    """
    results: List[R_Out] = []
    for args_item in args_list:
        if isinstance(args_item, tuple):
            results.append(func(*args_item))
        else:
            # This branch handles single arguments.
            # If func expects no arguments, args_item should be `()` and caught by `isinstance(tuple)`.
            # If func expects one argument, args_item is that argument.
            results.append(func(args_item))
    return results


def run_parallel(
    func: Callable[..., R_Out],
    args_list: Iterable[SingleTaskArgs],
    max_workers: Optional[int] = None,
    task_timeout: Optional[float] = None,
) -> List[Union[R_Out, Exception]]:
    """
    Executes a function in parallel for each set of arguments in args_list
    using a ThreadPoolExecutor. Results are returned in the same order as the input args_list.

    Args:
        func: The function to execute.
        args_list: An iterable of arguments (or argument tuples) to pass to func.
                   (See `run_sequentially` for formatting details).
        max_workers: The maximum number of worker threads. If None, it defaults
                     to ThreadPoolExecutor's default (typically based on CPU cores).
        task_timeout: The maximum number of seconds to wait for each individual task
                      to complete. If a task exceeds this timeout, a
                      concurrent.futures.TimeoutError will be stored as its result.
                      If None, tasks will wait indefinitely for completion.

    Returns:
        A list where each element corresponds to the respective item in args_list.
        - If a task executed successfully, its return value (R_Out) is stored.
        - If a task raised an exception (including TimeoutError due to task_timeout),
          the exception object itself is stored.
    """
    # Materialize args_list to ensure consistent ordering and count, especially if it's a generator.
    materialized_args_list = list(args_list)
    if not materialized_args_list:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: List[concurrent.futures.Future] = []
        for args_item in materialized_args_list:
            if isinstance(args_item, tuple):
                future = executor.submit(func, *args_item)
            else:
                future = executor.submit(func, args_item)
            futures.append(future)

        # Initialize results list. Type ignore is used because None is a placeholder.
        results: List[Union[R_Out, Exception]] = [None] * len(futures)  # type: ignore
        for i, future in enumerate(futures):
            try:
                results[i] = future.result(timeout=task_timeout)
            except Exception as e:  # Catches TimeoutError from future.result and any exception from func
                results[i] = e
        return results


def sequentialize():
    """
    Decorator to make a function that processes a single item (or argument set)
    able to process an iterable of items (or argument sets) sequentially.

    The decorated function will expect an iterable of argument sets as its
    primary argument and will return a list of results. If the underlying
    function raises an error, execution stops and the error propagates.

    Example:
        @sequentialize()
        def process_single(data, factor):
            return data * factor

        # Now call it with a list of argument tuples
        results = process_single([(1, 2), (3, 4)])
        # results will be [2, 12]
    """

    def decorator(
        func_to_process_single_item: Callable[..., R_Out],
    ) -> Callable[[Iterable[SingleTaskArgs]], List[R_Out]]:
        @functools.wraps(func_to_process_single_item)
        def wrapper(args_list_for_func: Iterable[SingleTaskArgs]) -> List[R_Out]:
            return run_sequentially(func_to_process_single_item, args_list_for_func)

        return wrapper

    return decorator


def parallelize(
    max_workers: Optional[int] = None, task_timeout: Optional[float] = None
):
    """
    Decorator to make a function that processes a single item (or argument set)
    able to process an iterable of items (or argument sets) in parallel.

    The decorated function will expect an iterable of argument sets as its
    primary argument and will return a list of results or exceptions,
    maintaining the original order.

    Args:
        max_workers (Optional[int]): Max worker threads for parallel execution.
        task_timeout (Optional[float]): Timeout for each individual task.

    Example:
        @parallelize(max_workers=4, task_timeout=5.0)
        def fetch_url_content(url: str) -> str:
            # ... implementation to fetch url ...
            return "content"

        # Now call it with a list of URLs
        results = fetch_url_content(["http://example.com", "http://example.org"])
        # results will be a list of contents or Exception objects.
    """

    def decorator(
        func_to_process_single_item: Callable[..., R_Out],
    ) -> Callable[[Iterable[SingleTaskArgs]], List[Union[R_Out, Exception]]]:
        @functools.wraps(func_to_process_single_item)
        def wrapper(
            args_list_for_func: Iterable[SingleTaskArgs],
        ) -> List[Union[R_Out, Exception]]:
            return run_parallel(
                func_to_process_single_item,
                args_list_for_func,
                max_workers=max_workers,
                task_timeout=task_timeout,
            )

        return wrapper

    return decorator


def typed_batch():
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

    def decorator(
        func: Callable[..., R_Out],
    ) -> Callable[[Iterable[SingleTaskArgs]], List[R_Out]]:
        @functools.wraps(func)
        def wrapper(args_list: Iterable[SingleTaskArgs]) -> List[R_Out]:
            return run_sequentially(func, args_list)

        # Preserve original function's type info while updating signature
        wrapper.__annotations__ = {
            "args_list": Iterable[SingleTaskArgs],
            "return": List[R_Out],
        }

        return cast(Callable[[Iterable[SingleTaskArgs]], List[R_Out]], wrapper)

    return decorator


def run_with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator that adds retry logic to functions. Essential for robust parallel
    processing when dealing with network calls, database operations, or other
    operations that might fail transiently.

    Args:
        max_attempts: Maximum number of attempts (including the first try).
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failed attempt.
        exceptions: Tuple of exception types to retry on. If None, retries on all exceptions.

    Example:
        @with_retry(max_attempts=3, delay=0.5, backoff=2.0, exceptions=(ConnectionError, TimeoutError))
        def fetch_data(url: str) -> dict:
            # This will retry up to 3 times with exponential backoff
            # only for ConnectionError and TimeoutError
            return requests.get(url).json()

        @parallelize(max_workers=10)
        @with_retry(max_attempts=2)
        def robust_fetch(url: str) -> str:
            return fetch_url_content(url)
    """
    if exceptions is None:
        exceptions = (Exception,)

    def decorator(func: Callable[..., R_Out]) -> Callable[..., R_Out]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> R_Out:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:  # Last attempt
                        break

                    print(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay:.2f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator
