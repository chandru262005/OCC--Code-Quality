from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """Execute analysis and return a standardized dictionary."""
        pass