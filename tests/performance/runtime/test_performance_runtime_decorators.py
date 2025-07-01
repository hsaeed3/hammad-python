import pytest
import concurrent.futures
from hammad.performance.runtime.decorators import (
    sequentialize_function,
    parallelize_function,
    update_batch_type_hints,
)


class TestPerformanceDecoratorsSequentializeFunction:
    def test_sequentialize_function(self):
        @sequentialize_function()
        def multiply(x, y):
            return x * y

        params = [(2, 3), (4, 5), (6, 7)]
        results = multiply(params)
        assert results == [6, 20, 42]

    def test_sequentialize_function_with_dict_params(self):
        @sequentialize_function()
        def add(a, b):
            return a + b

        params = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        results = add(params)
        assert results == [3, 7]


class TestPerformanceDecoratorsParallelizeFunction:
    def test_parallelize_function(self):
        @parallelize_function(max_workers=2)
        def multiply(x, y):
            return x * y

        params = [(2, 3), (4, 5), (6, 7)]
        results = multiply(params)
        assert results == [6, 20, 42]

    def test_parallelize_function_with_timeout(self):
        @parallelize_function(timeout=0.05)
        def slow_function(x):
            import time

            time.sleep(0.2)
            return x * 2

        params = [(1,), (2,)]
        results = slow_function(params)
        # Both tasks should timeout since they take 0.2s but timeout is 0.05s
        assert all(isinstance(r, Exception) for r in results)


class TestPerformanceDecoratorsUpdateBatchTypeHints:
    def test_update_batch_type_hints(self):
        @update_batch_type_hints()
        def process_item(x: int) -> str:
            return str(x)

        params = [(1,), (2,)]
        results = process_item(params)
        assert results == ["1", "2"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
