"""hammad.runtime.run"""

import concurrent.futures
import itertools
import functools
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
    overload,
)

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
)


__all__ = (
    "run_sequentially",
    "run_parallel",
    "run_with_retry",
)


Parameters = TypeVar("Parameters", bound=dict[str, Any])
Return = TypeVar("Return")

TaskParameters = TypeVar("TaskParameters", bound=dict[str, Any])


def run_sequentially(
    function: Callable[..., Return],
    parameters: Iterable[Parameters],
    raise_on_error: bool = False,
) -> List[Return]:
    """Executes a function multiple times sequentially, using a
    list of given parameter dictionary definitions.

    If the function raised an exception at any point during
    the call, by default the exception will be propogated/ignored
    and the run will continue, unless the `raise_on_error` flag is
    set to `True`.

    Args:
        function : The function to execute.
        parameters : An iterable of parameter dictionaries to pass to the function.
        raise_on_error : Whether to raise an exception if the function raises an exception.

    Returns:
        A list of results from the function calls."""
    results: List[Return] = []

    def execute_single_task(params: Parameters) -> Optional[Return]:
        """Execute a single task with error handling."""
        try:
            if isinstance(params, dict):
                return function(**params)
            else:
                # Handle case where params might be a single argument or tuple
                if isinstance(params, tuple):
                    return function(*params)
                else:
                    return function(params)
        except Exception as e:
            if raise_on_error:
                raise
            return None

    for params in itertools.chain(parameters):
        result = execute_single_task(params)
        if result is not None:
            results.append(result)

    return results


def run_parallel(
    function: Callable[..., Return],
    parameters: Iterable[Parameters],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
    raise_on_error: bool = False,
) -> List[Union[Return, Exception]]:
    """Executes a function multiple times in parallel, using a
    list of given parameter dictionary definitions.

    Uses ThreadPoolExecutor to run tasks concurrently. Results are returned
    in the same order as the input parameters.

    Args:
        function : The function to execute.
        parameters : An iterable of parameter dictionaries to pass to the function.
        max_workers : The maximum number of worker threads. If None, defaults
                     to ThreadPoolExecutor's default (typically based on CPU cores).
        timeout : The maximum number of seconds to wait for each individual task
                 to complete. If a task exceeds this timeout, a
                 concurrent.futures.TimeoutError will be stored as its result.
                 If None, tasks will wait indefinitely for completion.
        raise_on_error : Whether to raise an exception if the function raises an exception.
                        If False, exceptions are returned as results instead of being raised.

    Returns:
        A list where each element corresponds to the respective item in parameters.
        - If a task executed successfully, its return value is stored.
        - If a task raised an exception (including TimeoutError due to timeout),
          the exception object itself is stored (unless raise_on_error is True).
    """
    # Materialize parameters to ensure consistent ordering and count
    materialized_params = list(parameters)
    if not materialized_params:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: List[concurrent.futures.Future] = []

        # Submit all tasks
        for params in materialized_params:
            if isinstance(params, dict):
                future = executor.submit(function, **params)
            elif isinstance(params, tuple):
                future = executor.submit(function, *params)
            else:
                future = executor.submit(function, params)
            futures.append(future)

        # Collect results in order
        results: List[Union[Return, Exception]] = [None] * len(futures)  # type: ignore
        for i, future in enumerate(futures):
            try:
                results[i] = future.result(timeout=timeout)
            except Exception as e:
                if raise_on_error:
                    raise
                results[i] = e

        return results


@overload
def run_with_retry(
    func: Callable[..., Return],
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
    jitter: Optional[float] = None,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    reraise: bool = True,
    before_retry: Optional[Callable[[Exception], None]] = None,
    hook: Optional[Callable[[Exception, dict, dict], Tuple[dict, dict]]] = None,
) -> Callable[..., Return]: ...


@overload
def run_with_retry(
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
    jitter: Optional[float] = None,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    reraise: bool = True,
    before_retry: Optional[Callable[[Exception], None]] = None,
    hook: Optional[Callable[[Exception, dict, dict], Tuple[dict, dict]]] = None,
) -> Callable[[Callable[..., Return]], Callable[..., Return]]: ...


def run_with_retry(
    func: Optional[Callable[..., Return]] = None,
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
    jitter: Optional[float] = None,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    reraise: bool = True,
    before_retry: Optional[Callable[[Exception], None]] = None,
    hook: Optional[Callable[[Exception, dict, dict], Tuple[dict, dict]]] = None,
) -> Union[
    Callable[..., Return], Callable[[Callable[..., Return]], Callable[..., Return]]
]:
    """
    Decorator that adds retry logic to functions using tenacity. Essential for robust parallel
    processing when dealing with network calls, database operations, or other
    operations that might fail transiently.

    Can be used either as a decorator or as a function that takes a function as first argument.

    Args:
        func: The function to decorate (when used directly rather than as a decorator)
        max_attempts: Maximum number of attempts (including the first try).
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff: Multiplier for delay after each failed attempt.
        jitter: If set, adds random jitter to delays between retries.
        exceptions: Tuple of exception types to retry on. If None, retries on all exceptions.
        reraise: Whether to reraise the last exception after all retries fail.
        before_retry: Optional callback function to execute before each retry attempt.
                     Takes the exception as argument.
        hook: Optional function to modify args/kwargs before retry.
                   Takes (exception, current_args_dict, current_kwargs_dict) and
                   returns (new_args_dict, new_kwargs_dict).

    Example:
        # As a decorator:
        @run_with_retry(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
            backoff=2.0,
            exceptions=(ConnectionError, TimeoutError),
        )
        def fetch_data(url: str, timeout: int = 30) -> dict:
            return requests.get(url, timeout=timeout).json()

        # As a function:
        def fetch_data(url: str, timeout: int = 30) -> dict:
            return requests.get(url, timeout=timeout).json()

        fetch_with_retry = run_with_retry(fetch_data, max_attempts=3)
    """

    def decorator(f: Callable[..., Return]) -> Callable[..., Return]:
        # Create retry configuration
        wait_strategy = wait_exponential(
            multiplier=initial_delay,
            exp_base=backoff,
            max=max_delay,
        )

        # Build retry arguments
        retry_args = {
            "stop": stop_after_attempt(max_attempts),
            "wait": wait_strategy,
            "retry": retry_if_exception_type(exceptions)
            if exceptions
            else retry_if_exception(lambda e: True),
            "reraise": reraise,
        }

        if before_retry or hook:
            # We need a stateful wrapper to handle callbacks with hooks
            @functools.wraps(f)
            def wrapper(*args, **kwargs) -> Return:
                # Store current args/kwargs that can be modified by hook
                current_args = args
                current_kwargs = kwargs

                def before_sleep_callback(retry_state):
                    nonlocal current_args, current_kwargs

                    # Only process if there was an exception
                    if retry_state.outcome and retry_state.outcome.failed:
                        exc = retry_state.outcome.exception()

                        if before_retry:
                            before_retry(exc)

                        if hook:
                            # Convert args to dict for hook
                            args_dict = dict(enumerate(current_args))
                            # Call hook to potentially modify arguments
                            new_args_dict, new_kwargs = hook(
                                exc, args_dict, current_kwargs
                            )
                            # Convert back to args tuple
                            current_args = tuple(
                                new_args_dict[i] for i in range(len(new_args_dict))
                            )
                            current_kwargs = new_kwargs

                # Create a wrapped function that uses the current args/kwargs
                @retry(**retry_args, before_sleep=before_sleep_callback)
                def retryable_func():
                    return f(*current_args, **current_kwargs)

                return retryable_func()

            return wrapper
        else:
            # Simple case without callbacks - use tenacity's retry decorator directly
            return retry(**retry_args)(f)

    if func is not None:
        return decorator(func)
    return decorator
