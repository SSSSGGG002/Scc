from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    PROGRAM = auto()
    VAR = auto()
    INTEGER = auto()
    CHAR = auto()
    PROCEDURE = auto()
    BEGIN = auto()
    END = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FI = auto()
    WHILE = auto()
    DO = auto()
    ENDWH = auto()
    READ = auto()
    WRITE = auto()
    RETURN = auto()
    ID = auto()
    INTC = auto()
    CHARC = auto()
    STRINGC = auto()
    ASSIGN = auto()
    EQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    NEQ = auto()
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    DIVIDE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACK = auto()
    RBRACK = auto()
    SEMI = auto()
    COMMA = auto()
    DOT = auto()
    EOF = auto()


KEYWORDS = {
    "program": TokenType.PROGRAM,
    "var": TokenType.VAR,
    "integer": TokenType.INTEGER,
    "char": TokenType.CHAR,
    "procedure": TokenType.PROCEDURE,
    "begin": TokenType.BEGIN,
    "end": TokenType.END,
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "fi": TokenType.FI,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "endwh": TokenType.ENDWH,
    "read": TokenType.READ,
    "write": TokenType.WRITE,
    "return": TokenType.RETURN,
}


SINGLE_CHAR_TOKENS = {
    "=": TokenType.EQ,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.TIMES,
    "/": TokenType.DIVIDE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACK,
    "]": TokenType.RBRACK,
    ";": TokenType.SEMI,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int

    def __str__(self) -> str:
        return f"{self.line:>4}  {self.type.name:<10}  {self.lexeme}"
