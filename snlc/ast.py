from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class Program:
    name: str
    declarations: list["VarDecl"]
    procedures: list["ProcedureDecl"]
    body: list["Statement"]


@dataclass
class VarSpec:
    name: str
    size: int | None
    line: int


@dataclass
class VarDecl:
    type_name: str
    vars: list[VarSpec]
    line: int


@dataclass
class ParamSpec:
    name: str
    type_name: str
    is_ref: bool
    line: int


@dataclass
class ProcedureDecl:
    name: str
    params: list[ParamSpec]
    declarations: list["VarDecl"]
    procedures: list["ProcedureDecl"]
    body: list["Statement"]
    line: int


class Statement:
    line: int


class Expression:
    line: int


@dataclass
class AssignStmt(Statement):
    target: "Reference"
    value: Expression
    line: int


@dataclass
class ReadStmt(Statement):
    target: "Reference"
    line: int


@dataclass
class WriteStmt(Statement):
    value: Expression
    line: int


@dataclass
class CallStmt(Statement):
    name: str
    args: list[Expression]
    line: int


@dataclass
class ReturnStmt(Statement):
    value: Expression
    line: int


@dataclass
class IfStmt(Statement):
    condition: "Condition"
    then_body: list[Statement]
    else_body: list[Statement]
    line: int


@dataclass
class WhileStmt(Statement):
    condition: "Condition"
    body: list[Statement]
    line: int


@dataclass
class Condition:
    left: Expression
    operator: str
    right: Expression
    line: int


@dataclass
class BinaryExpr(Expression):
    left: Expression
    operator: str
    right: Expression
    line: int


@dataclass
class UnaryExpr(Expression):
    operator: str
    operand: Expression
    line: int


@dataclass
class VarRef(Expression):
    name: str
    line: int


@dataclass
class ArrayRef(Expression):
    name: str
    index: Expression
    line: int


@dataclass
class IntLiteral(Expression):
    value: int
    line: int


@dataclass
class CharLiteral(Expression):
    value: int
    display: str
    line: int


@dataclass
class StringLiteral(Expression):
    value: str
    line: int


Reference = Union[VarRef, ArrayRef]
