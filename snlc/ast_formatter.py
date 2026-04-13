from __future__ import annotations

from . import ast


class ASTFormatter:
    def format(self, program: ast.Program) -> str:
        self.lines: list[str] = []
        self._line(f"Program {program.name}")
        self._section("Declarations", 1, self._format_var_decls(program.declarations, 2))
        self._section("Procedures", 1, self._format_procedures(program.procedures, 2))
        self._line("Body", 1)
        self._format_statements(program.body, 2)
        return "\n".join(self.lines)

    def _format_var_decls(self, declarations: list[ast.VarDecl], indent: int) -> list[str]:
        lines: list[str] = []
        for decl in declarations:
            lines.append(self._indented(f"VarDecl {decl.type_name}", indent))
            for var in decl.vars:
                if var.size is None:
                    lines.append(self._indented(f"Var {var.name}", indent + 1))
                else:
                    lines.append(self._indented(f"Array {var.name}[{var.size}]", indent + 1))
        return lines

    def _format_procedures(self, procedures: list[ast.ProcedureDecl], indent: int) -> list[str]:
        lines: list[str] = []
        for proc in procedures:
            lines.append(self._indented(f"Procedure {proc.name}", indent))
            if proc.params:
                lines.append(self._indented("Params", indent + 1))
                for param in proc.params:
                    kind = "ref" if param.is_ref else "value"
                    lines.append(self._indented(f"Param {kind} {param.type_name} {param.name}", indent + 2))
            else:
                lines.append(self._indented("Params (empty)", indent + 1))

            decl_lines = self._format_var_decls(proc.declarations, indent + 2)
            if decl_lines:
                lines.append(self._indented("Declarations", indent + 1))
                lines.extend(decl_lines)

            nested_lines = self._format_procedures(proc.procedures, indent + 2)
            if nested_lines:
                lines.append(self._indented("Procedures", indent + 1))
                lines.extend(nested_lines)

            lines.append(self._indented("Body", indent + 1))
            body_formatter = ASTFormatter()
            body_formatter.lines = []
            body_formatter._format_statements(proc.body, indent + 2)
            lines.extend(body_formatter.lines)
        return lines

    def _format_statements(self, statements: list[ast.Statement], indent: int) -> None:
        for stmt in statements:
            self._format_statement(stmt, indent)

    def _format_statement(self, stmt: ast.Statement, indent: int) -> None:
        if isinstance(stmt, ast.AssignStmt):
            self._line("Assign", indent)
            self._line("Target", indent + 1)
            self._format_expr(stmt.target, indent + 2)
            self._line("Value", indent + 1)
            self._format_expr(stmt.value, indent + 2)
            return
        if isinstance(stmt, ast.ReadStmt):
            self._line("Read", indent)
            self._format_expr(stmt.target, indent + 1)
            return
        if isinstance(stmt, ast.WriteStmt):
            self._line("Write", indent)
            self._format_expr(stmt.value, indent + 1)
            return
        if isinstance(stmt, ast.CallStmt):
            self._line(f"Call {stmt.name}", indent)
            if stmt.args:
                self._line("Args", indent + 1)
                for arg in stmt.args:
                    self._format_expr(arg, indent + 2)
            else:
                self._line("Args (empty)", indent + 1)
            return
        if isinstance(stmt, ast.ReturnStmt):
            self._line("Return", indent)
            self._format_expr(stmt.value, indent + 1)
            return
        if isinstance(stmt, ast.IfStmt):
            self._line("If", indent)
            self._line(f"Condition {stmt.condition.operator}", indent + 1)
            self._line("Left", indent + 2)
            self._format_expr(stmt.condition.left, indent + 3)
            self._line("Right", indent + 2)
            self._format_expr(stmt.condition.right, indent + 3)
            self._line("Then", indent + 1)
            self._format_statements(stmt.then_body, indent + 2)
            self._line("Else", indent + 1)
            self._format_statements(stmt.else_body, indent + 2)
            return
        if isinstance(stmt, ast.WhileStmt):
            self._line("While", indent)
            self._line(f"Condition {stmt.condition.operator}", indent + 1)
            self._line("Left", indent + 2)
            self._format_expr(stmt.condition.left, indent + 3)
            self._line("Right", indent + 2)
            self._format_expr(stmt.condition.right, indent + 3)
            self._line("Body", indent + 1)
            self._format_statements(stmt.body, indent + 2)
            return
        raise TypeError(f"Unsupported statement: {type(stmt)!r}")

    def _format_expr(self, expr: ast.Expression, indent: int) -> None:
        if isinstance(expr, ast.VarRef):
            self._line(f"VarRef {expr.name}", indent)
            return
        if isinstance(expr, ast.ArrayRef):
            self._line(f"ArrayRef {expr.name}", indent)
            self._line("Index", indent + 1)
            self._format_expr(expr.index, indent + 2)
            return
        if isinstance(expr, ast.IntLiteral):
            self._line(f"Int {expr.value}", indent)
            return
        if isinstance(expr, ast.CharLiteral):
            self._line(f"Char {expr.display}", indent)
            return
        if isinstance(expr, ast.StringLiteral):
            self._line(f"String {expr.value!r}", indent)
            return
        if isinstance(expr, ast.UnaryExpr):
            self._line(f"Unary {expr.operator}", indent)
            self._format_expr(expr.operand, indent + 1)
            return
        if isinstance(expr, ast.BinaryExpr):
            self._line(f"Binary {expr.operator}", indent)
            self._line("Left", indent + 1)
            self._format_expr(expr.left, indent + 2)
            self._line("Right", indent + 1)
            self._format_expr(expr.right, indent + 2)
            return
        raise TypeError(f"Unsupported expression: {type(expr)!r}")

    def _section(self, title: str, indent: int, body_lines: list[str]) -> None:
        self._line(title, indent)
        if body_lines:
            self.lines.extend(body_lines)
        else:
            self._line("(empty)", indent + 1)

    def _line(self, text: str, indent: int = 0) -> None:
        self.lines.append(self._indented(text, indent))

    def _indented(self, text: str, indent: int) -> str:
        return f"{'  ' * indent}{text}"
