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