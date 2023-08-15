"""
Utilities for test files
"""
import unittest
from typing import Any, Callable, Dict
# DataSet is only here so type hints can be used.
DataSet = Dict[str, Any]


# Test runner decorator: Runs the test as a set of N SubTests,
# (where N is number of items in dataset), feeding the actual test
# function one test case at a time
def run_sub_tests_with_dataset(
    dataset: DataSet,
) -> Callable[[Callable], Callable]:
    """Decorator starting a unittest.TestCase.subtest() for each of the
    cases in dataset"""

    def real_decorator(
        function: Callable[[unittest.TestCase, Any], None]
    ) -> Callable[[unittest.TestCase], None]:
        def wrapper(test_cls: unittest.TestCase) -> None:
            for case, data in dataset.items():
                with test_cls.subTest(case=case):
                    # Save case name for future reference
                    test_cls.case_name = case.replace(" ", "_")
                    function(test_cls, data)

        return wrapper

    return real_decorator
