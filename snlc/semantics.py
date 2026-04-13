from __future__ import annotations

from dataclasses import dataclass, field

from . import ast
from .errors import CompileError


@dataclass
class Symbol:
    name: str
    type_name: str
    size: int | None
    line: int
    storage_name: str
    owner_proc: str | None = None
    is_param: bool = False
    is_ref: bool = False


@dataclass
class ProcedureSymbol:
    name: str
    qualified_name: str
    line: int
    params: list[Symbol] = field(default_factory=list)
    locals: list[Symbol] = field(default_factory=list)


@dataclass
class SemanticInfo:
    globals: dict[str, Symbol]
    all_symbols: dict[str, Symbol]
    procedures: dict[str, ProcedureSymbol]


@dataclass
class Scope:
    name: str
    qualified_name: str | None
    parent: Scope | None
    variables: dict[str, Symbol] = field(default_factory=dict)
    procedures: dict[str, ProcedureSymbol] = field(default_factory=dict)


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.global_symbols: dict[str, Symbol] = {}
        self.all_symbols: dict[str, Symbol] = {}
        self.procedures: dict[str, ProcedureSymbol] = {}

    def analyze(self, program: ast.Program) -> SemanticInfo:
        global_scope = Scope(program.name, None, None)
        self._declare_vars(program.declarations, global_scope)
        self._declare_procedures(program.procedures, global_scope)

        for proc in program.procedures:
            self._analyze_procedure(proc, global_scope)
        for stmt in program.body:
            self._check_stmt(stmt, global_scope, current_proc=None)

        return SemanticInfo(self.global_symbols, self.all_symbols, self.procedures)

    def _declare_vars(self, declarations: list[ast.VarDecl], scope: Scope) -> None:
        for decl in declarations:
            for var in decl.vars:
                self._ensure_name_available(var.name, scope, decl.line)
                if var.size is not None and var.size <= 0:
                    raise CompileError(f"Array '{var.name}' size must be positive", var.line)
                storage_name = var.name if scope.qualified_name is None else f"{scope.qualified_name}__{var.name}"
                symbol = Symbol(
                    name=var.name,
                    type_name=decl.type_name,
                    size=var.size,
                    line=decl.line,
                    storage_name=storage_name,
                    owner_proc=scope.qualified_name,
                )
                scope.variables[var.name] = symbol
                self.all_symbols[storage_name] = symbol
                if scope.parent is None:
                    self.global_symbols[var.name] = symbol

    def _declare_procedures(self, procedures: list[ast.ProcedureDecl], scope: Scope) -> None:
        for proc in procedures:
            self._ensure_name_available(proc.name, scope, proc.line)
            qualified_name = proc.name if scope.qualified_name is None else f"{scope.qualified_name}__{proc.name}"
            symbol = ProcedureSymbol(proc.name, qualified_name, proc.line)
            scope.procedures[proc.name] = symbol
            self.procedures[qualified_name] = symbol
            proc.symbol = symbol

    def _analyze_procedure(self, proc: ast.ProcedureDecl, parent_scope: Scope) -> None:
        proc_symbol: ProcedureSymbol = proc.symbol
        scope = Scope(proc.name, proc_symbol.qualified_name, parent_scope)

        for param in proc.params:
            self._ensure_name_available(param.name, scope, param.line)
            storage_name = f"{scope.qualified_name}__{param.name}"
            symbol = Symbol(
                name=param.name,
                type_name=param.type_name,
                size=None,
                line=param.line,
                storage_name=storage_name,
                owner_proc=scope.qualified_name,
                is_param=True,
                is_ref=param.is_ref,
            )
            scope.variables[param.name] = symbol
            proc_symbol.params.append(symbol)
            proc_symbol.locals.append(symbol)
            self.all_symbols[storage_name] = symbol
            param.symbol = symbol

        self._declare_vars(proc.declarations, scope)
        for symbol in scope.variables.values():
            if not symbol.is_param:
                proc_symbol.locals.append(symbol)

        self._declare_procedures(proc.procedures, scope)
        for nested in proc.procedures:
            self._analyze_procedure(nested, scope)
        for stmt in proc.body:
            self._check_stmt(stmt, scope, current_proc=proc_symbol)

    def _check_stmt(self, stmt: ast.Statement, scope: Scope, current_proc: ProcedureSymbol | None) -> None:
        if isinstance(stmt, ast.AssignStmt):
            symbol = self._check_reference(stmt.target, scope)
            expr_type = self._check_expr(stmt.value, scope)
            if symbol.type_name != expr_type:
                raise CompileError(
                    f"Cannot assign {expr_type} value to {symbol.type_name} target '{self._reference_name(stmt.target)}'",
                    stmt.line,
                )
            return

        if isinstance(stmt, ast.ReadStmt):
            self._check_reference(stmt.target, scope)
            return

        if isinstance(stmt, ast.WriteStmt):
            self._check_expr(stmt.value, scope)
            return

        if isinstance(stmt, ast.CallStmt):
            proc_symbol = self._lookup_procedure(stmt.name, stmt.line, scope)
            stmt.procedure = proc_symbol
            if len(stmt.args) != len(proc_symbol.params):
                raise CompileError(
                    f"Procedure '{stmt.name}' expects {len(proc_symbol.params)} argument(s), got {len(stmt.args)}",
                    stmt.line,
                )
            for arg, param in zip(stmt.args, proc_symbol.params):
                arg_type = self._check_expr(arg, scope)
                if arg_type != param.type_name:
                    raise CompileError(
                        f"Procedure '{stmt.name}' argument for parameter '{param.name}' must be {param.type_name}",
                        stmt.line,
                    )
                if param.is_ref and not isinstance(arg, (ast.VarRef, ast.ArrayRef)):
                    raise CompileError(
                        f"Procedure '{stmt.name}' parameter '{param.name}' requires a variable reference",
                        stmt.line,
                    )
            return

        if isinstance(stmt, ast.ReturnStmt):
            if current_proc is None:
                raise CompileError("return() can only appear inside a procedure", stmt.line)
            self._check_expr(stmt.value, scope)
            stmt.procedure = current_proc
            return

        if isinstance(stmt, ast.IfStmt):
            self._check_condition(stmt.condition, scope)
            for nested in stmt.then_body:
                self._check_stmt(nested, scope, current_proc)
            for nested in stmt.else_body:
                self._check_stmt(nested, scope, current_proc)
            return

        if isinstance(stmt, ast.WhileStmt):
            self._check_condition(stmt.condition, scope)
            for nested in stmt.body:
                self._check_stmt(nested, scope, current_proc)
            return

        raise CompileError("Unsupported statement", stmt.line)

    def _check_condition(self, cond: ast.Condition, scope: Scope) -> None:
        left_type = self._check_expr(cond.left, scope)
        right_type = self._check_expr(cond.right, scope)
        if left_type == "string" or right_type == "string":
            raise CompileError("String values can only be used with write()", cond.line)
        if cond.operator == "<":
            if left_type != "integer" or right_type != "integer":
                raise CompileError("Operator '<' requires integer operands", cond.line)
            return
        if cond.operator == "<=":
            if left_type != "integer" or right_type != "integer":
                raise CompileError("Operator '<=' requires integer operands", cond.line)
            return
        if cond.operator == ">":
            if left_type != "integer" or right_type != "integer":
                raise CompileError("Operator '>' requires integer operands", cond.line)
            return
        if cond.operator == ">=":
            if left_type != "integer" or right_type != "integer":
                raise CompileError("Operator '>=' requires integer operands", cond.line)
            return
        if left_type != right_type:
            raise CompileError(f"Operator '{cond.operator}' requires operands of the same type", cond.line)

    def _check_expr(self, expr: ast.Expression, scope: Scope) -> str:
        if isinstance(expr, ast.IntLiteral):
            expr.inferred_type = "integer"
            return expr.inferred_type
        if isinstance(expr, ast.CharLiteral):
            expr.inferred_type = "char"
            return expr.inferred_type
        if isinstance(expr, ast.StringLiteral):
            expr.inferred_type = "string"
            return expr.inferred_type
        if isinstance(expr, ast.VarRef):
            symbol = self._lookup_variable(expr.name, expr.line, scope)
            if symbol.size is not None:
                raise CompileError(f"Array '{expr.name}' must be indexed before use", expr.line)
            expr.inferred_type = symbol.type_name
            expr.symbol = symbol
            return expr.inferred_type
        if isinstance(expr, ast.ArrayRef):
            symbol = self._lookup_variable(expr.name, expr.line, scope)
            if symbol.size is None:
                raise CompileError(f"Identifier '{expr.name}' is not an array", expr.line)
            index_type = self._check_expr(expr.index, scope)
            if index_type != "integer":
                raise CompileError("Array index must be an integer", expr.line)
            if isinstance(expr.index, ast.IntLiteral) and not 0 <= expr.index.value < symbol.size:
                raise CompileError(
                    f"Array index {expr.index.value} out of bounds for '{expr.name}' of size {symbol.size}",
                    expr.line,
                )
            expr.inferred_type = symbol.type_name
            expr.symbol = symbol
            return expr.inferred_type
        if isinstance(expr, ast.UnaryExpr):
            operand_type = self._check_expr(expr.operand, scope)
            if operand_type != "integer":
                raise CompileError(f"Operator '{expr.operator}' requires integer operands", expr.line)
            expr.inferred_type = "integer"
            return expr.inferred_type
        if isinstance(expr, ast.BinaryExpr):
            left_type = self._check_expr(expr.left, scope)
            right_type = self._check_expr(expr.right, scope)
            if left_type != "integer" or right_type != "integer":
                raise CompileError(f"Operator '{expr.operator}' requires integer operands", expr.line)
            expr.inferred_type = "integer"
            return expr.inferred_type
        raise CompileError("Unsupported expression", expr.line)

    def _lookup_variable(self, name: str, line: int, scope: Scope) -> Symbol:
        current: Scope | None = scope
        while current is not None:
            symbol = current.variables.get(name)
            if symbol is not None:
                return symbol
            current = current.parent
        raise CompileError(f"Identifier '{name}' is not declared", line)

    def _lookup_procedure(self, name: str, line: int, scope: Scope) -> ProcedureSymbol:
        current: Scope | None = scope
        while current is not None:
            symbol = current.procedures.get(name)
            if symbol is not None:
                return symbol
            current = current.parent
        raise CompileError(f"Procedure '{name}' is not declared", line)

    def _check_reference(self, ref: ast.Reference, scope: Scope) -> Symbol:
        symbol = self._lookup_variable(ref.name, ref.line, scope)
        ref.symbol = symbol
        if isinstance(ref, ast.VarRef):
            if symbol.size is not None:
                raise CompileError(f"Array '{ref.name}' must be indexed before use", ref.line)
            return symbol
        if symbol.size is None:
            raise CompileError(f"Identifier '{ref.name}' is not an array", ref.line)
        index_type = self._check_expr(ref.index, scope)
        if index_type != "integer":
            raise CompileError("Array index must be an integer", ref.line)
        if isinstance(ref.index, ast.IntLiteral) and not 0 <= ref.index.value < symbol.size:
            raise CompileError(
                f"Array index {ref.index.value} out of bounds for '{ref.name}' of size {symbol.size}",
                ref.line,
            )
        return symbol

    def _reference_name(self, ref: ast.Reference) -> str:
        if isinstance(ref, ast.VarRef):
            return ref.name
        return f"{ref.name}[...]"

    def _ensure_name_available(self, name: str, scope: Scope, line: int) -> None:
        if name in scope.variables or name in scope.procedures:
            raise CompileError(f"Identifier '{name}' redefined", line)
