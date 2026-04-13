from __future__ import annotations


class CompileError(Exception):
    """Base exception for compile-time failures."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.message = message
        self.line = line
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        return f"Line {self.line}: {self.message}"
