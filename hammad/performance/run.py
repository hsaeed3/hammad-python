"""hammad.performance.run"""

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
    cast,
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


def run_with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: float = 2.0,
    jitter: Optional[float] = None,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    reraise: bool = True,
    before_retry: Optional[Callable[[Exception], None]] = None,
    hook: Optional[Callable[[Exception, dict, dict], Tuple[dict, dict]]] = None,
):
    """
    Decorator that adds retry logic to functions using tenacity. Essential for robust parallel
    processing when dealing with network calls, database operations, or other
    operations that might fail transiently.

    Args:
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
        def modify_params(e, args, kwargs):
            if isinstance(e, TimeoutError):
                kwargs['timeout'] = kwargs.get('timeout', 30) * 2
            return args, kwargs

        @run_with_retry(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
            backoff=2.0,
            exceptions=(ConnectionError, TimeoutError),
            before_retry=lambda e: print(f"Retrying due to: {e}"),
            hook=modify_params
        )
        def fetch_data(url: str, timeout: int = 30) -> dict:
            return requests.get(url, timeout=timeout).json()
    """

    def decorator(func: Callable[..., Return]) -> Callable[..., Return]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Return:
            # Convert args to dict for easier manipulation
            args_dict = dict(enumerate(args))

            def modified_func(**all_kwargs):
                # Extract positional args back from dict
                current_args = [all_kwargs.pop(i) for i in range(len(args_dict))]
                return func(*current_args, **all_kwargs)

            # Combine all parameters into kwargs for the retry hook
            all_kwargs = {**args_dict, **kwargs}

            def before_retry_with_hook(retry_state):
                if before_retry:
                    before_retry(retry_state.outcome.exception())

                if hook:
                    nonlocal all_kwargs
                    args_dict, kwargs_dict = hook(
                        retry_state.outcome.exception(),
                        {i: all_kwargs[i] for i in range(len(args_dict))},
                        {k: v for k, v in all_kwargs.items() if not isinstance(k, int)},
                    )
                    all_kwargs = {**args_dict, **kwargs_dict}

                return all_kwargs

            retry_config = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=initial_delay,
                    exp_base=backoff,
                    max=max_delay,
                    jitter=jitter,
                ),
                retry=retry_if_exception_type(exceptions)
                if exceptions
                else retry_if_exception,
                reraise=reraise,
                before_sleep=before_retry_with_hook if (before_retry or hook) else None,
            )

            return retry_config(modified_func)(**all_kwargs)

        return wrapper

    return decorator
