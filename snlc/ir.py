from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import ast
from .errors import CompileError
from .semantics import SemanticInfo


Operand = Any


@dataclass(frozen=True)
class ArrayAccess:
    name: str
    index: Operand

    def __str__(self) -> str:
        return f"{self.name}[{self.index}]"


@dataclass(frozen=True)
class AddressOf:
    target: Operand

    def __str__(self) -> str:
        return f"&{self.target}"


@dataclass
class Quadruple:
    index: int
    op: str
    arg1: Operand
    arg2: Operand
    result: Operand

    def format_operand(self, value: Operand) -> str:
        if value is None:
            return "_"
        if isinstance(value, (ArrayAccess, AddressOf)):
            return str(value)
        return str(value)

    def __str__(self) -> str:
        return (
            f"{self.index:>3}: "
            f"({self.op}, {self.format_operand(self.arg1)}, "
            f"{self.format_operand(self.arg2)}, {self.format_operand(self.result)})"
        )


class IRGenerator:
    def __init__(self, semantic_info: SemanticInfo) -> None:
        self.semantic_info = semantic_info
        self.quads: list[Quadruple] = []
        self.temp_count = 0
        self.label_count = 0
        self.temp_types: dict[str, str] = {}
        self.string_count = 0
        self.string_literals: dict[str, str] = {}
        self.current_context = "main"
        self.current_proc: str | None = None

    def generate(self, program: ast.Program) -> tuple[list[Quadruple], dict[str, str], dict[str, str]]:
        self.current_context = "main"
        self.current_proc = None
        for stmt in program.body:
            self._gen_stmt(stmt)
        for proc in program.procedures:
            self._gen_procedure(proc)
        return self.quads, self.temp_types, self.string_literals

    def _emit(self, op: str, arg1: Operand = None, arg2: Operand = None, result: Operand = None) -> None:
        self.quads.append(Quadruple(len(self.quads), op, arg1, arg2, result))

    def _new_temp(self, type_name: str) -> str:
        self.temp_count += 1
        name = f"t{self.temp_count}" if self.current_proc is None else f"{self.current_context}__t{self.temp_count}"
        self.temp_types[name] = type_name
        return name

    def _new_label(self) -> str:
        self.label_count += 1
        prefix = "L" if self.current_proc is None else f"{self.current_context}_L"
        return f"{prefix}{self.label_count}"

    def _new_string(self, value: str) -> str:
        self.string_count += 1
        name = f"s{self.string_count}"
        self.string_literals[name] = value
        return name

    def _gen_procedure(self, proc: ast.ProcedureDecl) -> None:
        proc_name = proc.symbol.qualified_name
        saved_context = self.current_context
        saved_proc = self.current_proc
        self.current_context = proc_name
        self.current_proc = proc_name
        self._emit("proc", None, None, proc_name)
        for stmt in proc.body:
            self._gen_stmt(stmt)
        self._emit("endproc", None, None, proc_name)
        for nested in proc.procedures:
            self._gen_procedure(nested)
        self.current_context = saved_context
        self.current_proc = saved_proc

    def _gen_stmt(self, stmt: ast.Statement) -> None:
        if isinstance(stmt, ast.AssignStmt):
            value = self._gen_expr(stmt.value)
            self._emit("assign", value, None, self._gen_reference(stmt.target))
            return

        if isinstance(stmt, ast.ReadStmt):
            type_name = stmt.target.symbol.type_name
            self._emit("read", type_name, None, self._gen_reference(stmt.target))
            return

        if isinstance(stmt, ast.WriteStmt):
            value = self._gen_expr(stmt.value)
            self._emit("write", value, getattr(stmt.value, "inferred_type", None), None)
            return

        if isinstance(stmt, ast.CallStmt):
            for arg, param in zip(stmt.args, stmt.procedure.params):
                if param.is_ref:
                    self._emit("param_ref", AddressOf(self._gen_reference(arg)), None, param.storage_name)
                else:
                    self._emit("param", self._gen_expr(arg), None, param.storage_name)
            self._emit("call", None, None, stmt.procedure.qualified_name)
            return

        if isinstance(stmt, ast.ReturnStmt):
            self._emit("return", None, None, stmt.procedure.qualified_name)
            return

        if isinstance(stmt, ast.IfStmt):
            else_label = self._new_label()
            end_label = self._new_label()
            self._emit_false_jump(stmt.condition, else_label)
            for nested in stmt.then_body:
                self._gen_stmt(nested)
            self._emit("goto", None, None, end_label)
            self._emit("label", None, None, else_label)
            for nested in stmt.else_body:
                self._gen_stmt(nested)
            self._emit("label", None, None, end_label)
            return

        if isinstance(stmt, ast.WhileStmt):
            start_label = self._new_label()
            end_label = self._new_label()
            self._emit("label", None, None, start_label)
            self._emit_false_jump(stmt.condition, end_label)
            for nested in stmt.body:
                self._gen_stmt(nested)
            self._emit("goto", None, None, start_label)
            self._emit("label", None, None, end_label)
            return

        raise TypeError(f"Unsupported statement: {type(stmt)!r}")

    def _emit_false_jump(self, cond: ast.Condition, false_label: str) -> None:
        left = self._gen_expr(cond.left)
        right = self._gen_expr(cond.right)
        if isinstance(left, int) and isinstance(right, int):
            if not self._evaluate_condition(cond.operator, left, right):
                self._emit("goto", None, None, false_label)
            return
        false_jump_map = {
            "<": "bge",
            "<=": "bgt",
            ">": "ble",
            ">=": "blt",
            "=": "bne",
            "<>": "beq",
        }
        self._emit(false_jump_map[cond.operator], left, right, false_label)

    def _gen_expr(self, expr: ast.Expression) -> Operand:
        if isinstance(expr, ast.IntLiteral):
            return expr.value
        if isinstance(expr, ast.CharLiteral):
            return expr.value
        if isinstance(expr, ast.StringLiteral):
            return self._new_string(expr.value)
        if isinstance(expr, ast.VarRef):
            return expr.symbol.storage_name
        if isinstance(expr, ast.ArrayRef):
            return self._gen_reference(expr)
        if isinstance(expr, ast.UnaryExpr):
            operand = self._gen_expr(expr.operand)
            if isinstance(operand, int):
                return -operand
            temp = self._new_temp("integer")
            self._emit("sub", 0, operand, temp)
            return temp
        if isinstance(expr, ast.BinaryExpr):
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            if isinstance(left, int) and isinstance(right, int):
                return self._fold_binary(expr.operator, left, right, expr.line)
            temp = self._new_temp("integer")
            op_map = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
            self._emit(op_map[expr.operator], left, right, temp)
            return temp
        raise TypeError(f"Unsupported expression: {type(expr)!r}")

    def _gen_reference(self, ref: ast.Reference) -> Operand:
        if isinstance(ref, ast.VarRef):
            return ref.symbol.storage_name
        index = self._gen_expr(ref.index)
        return ArrayAccess(ref.symbol.storage_name, index)

    def _fold_binary(self, operator: str, left: int, right: int, line: int) -> int:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise CompileError("Division by zero in constant expression", line)
            return left // right
        raise ValueError(f"Unsupported binary operator '{operator}'")

    def _evaluate_condition(self, operator: str, left: int, right: int) -> bool:
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "=":
            return left == right
        if operator == "<>":
            return left != right
        raise ValueError(f"Unsupported relational operator '{operator}'")
