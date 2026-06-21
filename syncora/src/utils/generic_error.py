from enum import Enum


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class SyncoraError(Exception):
    def __init__(self, message: str, error_code: int = 0, severity: Severity = Severity.HIGH) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        
    def __str__(self) -> str:
        return f"Error {self.error_code} (Severity: {self.severity.name}): {self.message}"


class ItemNotFoundError(SyncoraError):
    def __init__(self, item_type: str, item_id: str, search_space: str, error_code: int = 400) -> None:
        super().__init__(
            f"Item {item_type}:{item_id} not found in {search_space}",
            error_code,
            Severity.MEDIUM
        )