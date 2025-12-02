from abc import ABC, abstractmethod


class BaseWorkFlow(ABC):
    @abstractmethod
    def run(self) -> bool:
        """
        Run the workflow.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")
