from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ast import Program
from .ast_formatter import ASTFormatter
from .ir import IRGenerator, Quadruple
from .lexer import Lexer
from .mips import MIPSGenerator
from .parser import Parser
from .semantics import SemanticAnalyzer, Symbol
from .tokens import Token


@dataclass
class CompilationResult:
    tokens: list[Token]
    program: Program
    symbols: dict[str, Symbol]
    all_symbols: dict[str, Symbol]
    quadruples: list[Quadruple]
    mips: str
    temp_types: dict[str, str]
    string_literals: dict[str, str]

    def format_tokens(self) -> str:
        return "\n".join(str(token) for token in self.tokens)

    def format_quads(self) -> str:
        return "\n".join(str(quad) for quad in self.quadruples)

    def format_ast(self) -> str:
        return ASTFormatter().format(self.program)


def compile_source(source: str) -> CompilationResult:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    semantic_info = analyzer.analyze(program)
    ir_generator = IRGenerator(semantic_info)
    quads, temp_types, string_literals = ir_generator.generate(program)
    mips = MIPSGenerator(semantic_info, temp_types, quads, string_literals).generate()
    return CompilationResult(
        tokens,
        program,
        semantic_info.globals,
        semantic_info.all_symbols,
        quads,
        mips,
        temp_types,
        string_literals,
    )


def compile_file(path: str | Path) -> CompilationResult:
    return compile_source(Path(path).read_text(encoding="utf-8"))
