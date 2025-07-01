import pytest
from hammad.performance.runtime.run import (
    run_sequentially,
    run_parallel,
    run_with_retry,
)


class TestPerformanceRunSequentially:
    def test_run_sequentially(self):
        def multiply(x, y):
            return x * y

        params = [(2, 3), (4, 5), (6, 7)]
        results = run_sequentially(multiply, params)
        assert results == [6, 20, 42]

    def test_run_sequentially_with_dict_params(self):
        def add(a, b):
            return a + b

        params = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        results = run_sequentially(add, params)
        assert results == [3, 7]

    def test_run_sequentially_with_error(self):
        def divide(x, y):
            return x / y

        params = [(6, 2), (4, 0), (10, 5)]

        # Without raise_on_error, continues after error
        results = run_sequentially(divide, params, raise_on_error=False)
        assert results == [3.0, 2.0]

        # With raise_on_error=True, raises the exception
        with pytest.raises(ZeroDivisionError):
            run_sequentially(divide, params, raise_on_error=True)


class TestPerformanceRunParallel:
    def test_run_parallel(self):
        def square(x):
            return x * x

        params = [2, 3, 4]
        results = run_parallel(square, params)
        assert results == [4, 9, 16]

    def test_run_parallel_with_error(self):
        def reciprocal(x):
            return 1 / x

        params = [2, 0, 4]

        # Without raise_on_error, returns exceptions in results
        results = run_parallel(reciprocal, params, raise_on_error=False)
        assert isinstance(results[0], float)
        assert isinstance(results[1], ZeroDivisionError)
        assert isinstance(results[2], float)

        # With raise_on_error=True, raises the first exception
        with pytest.raises(ZeroDivisionError):
            run_parallel(reciprocal, params, raise_on_error=True)


class TestPerformanceRunWithRetry:
    def test_run_with_retry(self):
        attempts = 0

        @run_with_retry(max_attempts=3, initial_delay=0.1)
        def flaky_function():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert attempts == 3

    def test_run_with_retry_max_attempts(self):
        attempts = 0

        @run_with_retry(max_attempts=2, initial_delay=0.1)
        def always_fails():
            nonlocal attempts
            attempts += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fails()
        assert attempts == 2


if __name__ == "__main__":
    pytest.main(["-v", __file__])
