"""
Utilities for test files
"""
import os
import unittest
from typing import Any, Callable
import requests

IPFS_API_URL = "http://localhost:5001/api/v0"
TEST_FILES_PATH = 'test_files'

def _upload_to_ipfs(filepath: str) -> str:
    with open(filepath, "rb") as file:
        response = requests.post(f"{IPFS_API_URL}/add", files={"file": file}, timeout=5)

    response_json = response.json()
    cid = response_json["Hash"]
    return cid

def run_sub_tests_with_test_files() -> Callable[[Callable], Callable]:
    """Decorator starting a unittest.TestCase.subtest() for each of the
    files in test_files"""

    def real_decorator(
        function: Callable[[unittest.TestCase, Any], None]
    ) -> Callable[[unittest.TestCase], None]:
        def wrapper(test_cls: unittest.TestCase) -> None:
            try:
                items = os.listdir(TEST_FILES_PATH)
                for item in items:
                    filepath = os.path.join(TEST_FILES_PATH, item)
                    if os.path.isfile(filepath):
                        cid = _upload_to_ipfs(filepath)
                        with open(filepath, "rb") as file:
                            file_bytes = file.read()

                        function(test_cls, cid, item, file_bytes)
            except OSError as ex:
                print(f"Error reading directory: {ex}")
                return

        return wrapper

    return real_decorator
