import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_clean_code():
    """Well-written Python code that should score high."""
    return '''
def add(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers and return the result."""
    return a * b


class Calculator:
    """A simple calculator class."""

    def __init__(self) -> None:
        self.history: list[float] = []

    def compute(self, a: float, b: float, op: str = "add") -> float:
        """Perform a computation and store the result."""
        if op == "add":
            result = a + b
        elif op == "multiply":
            result = a * b
        else:
            raise ValueError(f"Unknown operation: {op}")
        self.history.append(result)
        return result
'''


@pytest.fixture
def sample_buggy_code():
    """Code with lint issues and complexity that should score low."""
    return """
import os
import sys
import json  # unused

def x(a,b,c,d,e,f,g):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return f
    return None
"""


@pytest.fixture
def sample_insecure_code():
    """Code with security issues that should score very low."""
    return """
import os

password = "super_secret_123"
api_key = "sk-12345abcde"

def dangerous_function(user_input):
    eval(user_input)
    os.system("rm -rf " + user_input)
    return True
"""


@pytest.fixture
def sample_file_path(tmp_path, sample_clean_code):
    """Create a temporary Python file with clean code."""
    p = tmp_path / "test_file.py"
    p.write_text(sample_clean_code)
    return str(p)


@pytest.fixture
def buggy_file_path(tmp_path, sample_buggy_code):
    """Create a temporary Python file with buggy code."""
    p = tmp_path / "buggy_file.py"
    p.write_text(sample_buggy_code)
    return str(p)


@pytest.fixture
def insecure_file_path(tmp_path, sample_insecure_code):
    """Create a temporary Python file with insecure code."""
    p = tmp_path / "insecure_file.py"
    p.write_text(sample_insecure_code)
    return str(p)
