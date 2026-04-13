from __future__ import annotations

from .errors import CompileError
from .tokens import KEYWORDS, SINGLE_CHAR_TOKENS, Token, TokenType


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0
        self.line = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._is_at_end():
            ch = self._peek()

            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self._advance()
                self.line += 1
                continue
            if ch == "{":
                self._skip_comment()
                continue
            if ch.isalpha():
                tokens.append(self._identifier())
                continue
            if ch.isdigit():
                tokens.append(self._number())
                continue
            if ch == "'":
                tokens.append(self._char_literal())
                continue
            if ch == "\"":
                tokens.append(self._string_literal())
                continue
            if ch == ":":
                tokens.append(self._assign())
                continue
            if ch == "<":
                tokens.append(self._less_family())
                continue
            if ch == ">":
                tokens.append(self._greater_family())
                continue
            if ch in SINGLE_CHAR_TOKENS:
                tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, self.line))
                self._advance()
                continue
            raise CompileError(f"Illegal character '{ch}'", self.line)

        tokens.append(Token(TokenType.EOF, "EOF", self.line))
        return tokens

    def _identifier(self) -> Token:
        start = self.index
        line = self.line
        while not self._is_at_end() and self._peek().isalnum():
            self._advance()
        lexeme = self.source[start:self.index]
        return Token(KEYWORDS.get(lexeme.lower(), TokenType.ID), lexeme, line)

    def _number(self) -> Token:
        start = self.index
        line = self.line
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()
        return Token(TokenType.INTC, self.source[start:self.index], line)

    def _char_literal(self) -> Token:
        line = self.line
        self._advance()
        if self._is_at_end() or self._peek() == "\n":
            raise CompileError("Unterminated character literal", line)
        value = self._advance()
        if self._is_at_end() or self._peek() != "'":
            raise CompileError("Character literal must contain exactly one character", line)
        self._advance()
        return Token(TokenType.CHARC, value, line)

    def _string_literal(self) -> Token:
        line = self.line
        self._advance()
        chars: list[str] = []

        while not self._is_at_end():
            ch = self._peek()
            if ch == "\"":
                self._advance()
                return Token(TokenType.STRINGC, "".join(chars), line)
            if ch == "\n":
                raise CompileError("Unterminated string literal", line)
            if ch == "\\":
                self._advance()
                if self._is_at_end():
                    raise CompileError("Unterminated string literal", line)
                escaped = self._advance()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "\"": "\"",
                    "\\": "\\",
                }
                if escaped not in escape_map:
                    raise CompileError(f"Unsupported escape '\\{escaped}'", line)
                chars.append(escape_map[escaped])
                continue
            chars.append(self._advance())

        raise CompileError("Unterminated string literal", line)

    def _assign(self) -> Token:
        line = self.line
        self._advance()
        if self._is_at_end() or self._peek() != "=":
            raise CompileError("Expected '=' after ':'", line)
        self._advance()
        return Token(TokenType.ASSIGN, ":=", line)

    def _less_family(self) -> Token:
        line = self.line
        self._advance()
        if not self._is_at_end():
            if self._peek() == "=":
                self._advance()
                return Token(TokenType.LE, "<=", line)
            if self._peek() == ">":
                self._advance()
                return Token(TokenType.NEQ, "<>", line)
        return Token(TokenType.LT, "<", line)

    def _greater_family(self) -> Token:
        line = self.line
        self._advance()
        if not self._is_at_end() and self._peek() == "=":
            self._advance()
            return Token(TokenType.GE, ">=", line)
        return Token(TokenType.GT, ">", line)

    def _skip_comment(self) -> None:
        start_line = self.line
        self._advance()
        while not self._is_at_end() and self._peek() != "}":
            if self._peek() == "\n":
                self.line += 1
            self._advance()
        if self._is_at_end():
            raise CompileError("Unterminated comment", start_line)
        self._advance()

    def _peek(self) -> str:
        return self.source[self.index]

    def _advance(self) -> str:
        ch = self.source[self.index]
        self.index += 1
        return ch

    def _is_at_end(self) -> bool:
        return self.index >= len(self.source)
