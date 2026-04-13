from __future__ import annotations

from . import ast
from .errors import CompileError
from .tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> ast.Program:
        self._expect(TokenType.PROGRAM, "Expected 'program'")
        name = self._expect(TokenType.ID, "Expected program name")
        declarations, procedures = self._parse_declare_part()
        body = self._parse_program_body()
        self._expect(TokenType.DOT, "Expected '.' after program body")
        self._expect(TokenType.EOF, "Unexpected tokens after program end")
        return ast.Program(name.lexeme, declarations, procedures, body)

    def _parse_declare_part(self) -> tuple[list[ast.VarDecl], list[ast.ProcedureDecl]]:
        declarations = self._parse_declarations()
        procedures = self._parse_procedures()
        return declarations, procedures

    def _parse_declarations(self) -> list[ast.VarDecl]:
        declarations: list[ast.VarDecl] = []
        if self._match(TokenType.VAR):
            while self._check(TokenType.INTEGER) or self._check(TokenType.CHAR):
                declarations.append(self._parse_var_decl())
        return declarations

    def _parse_procedures(self) -> list[ast.ProcedureDecl]:
        procedures: list[ast.ProcedureDecl] = []
        while self._check(TokenType.PROCEDURE):
            procedures.append(self._parse_procedure_decl())
        return procedures

    def _parse_var_decl(self) -> ast.VarDecl:
        type_token = self._advance()
        vars_ = [self._parse_var_spec()]
        while self._match(TokenType.COMMA):
            vars_.append(self._parse_var_spec())
        self._expect(TokenType.SEMI, "Expected ';' after declaration")
        return ast.VarDecl(type_token.lexeme.lower(), vars_, type_token.line)

    def _parse_var_spec(self) -> ast.VarSpec:
        name = self._expect(TokenType.ID, "Expected identifier in declaration")
        size: int | None = None
        if self._match(TokenType.LBRACK):
            size_token = self._expect(TokenType.INTC, "Expected array size")
            size = int(size_token.lexeme)
            self._expect(TokenType.RBRACK, "Expected ']' after array size")
        return ast.VarSpec(name.lexeme, size, name.line)

    def _parse_program_body(self) -> list[ast.Statement]:
        self._expect(TokenType.BEGIN, "Expected 'begin'")
        body = self._parse_statement_list({TokenType.END})
        self._expect(TokenType.END, "Expected 'end'")
        return body

    def _parse_procedure_decl(self) -> ast.ProcedureDecl:
        keyword = self._expect(TokenType.PROCEDURE, "Expected 'procedure'")
        name = self._expect(TokenType.ID, "Expected procedure name")
        self._expect(TokenType.LPAREN, "Expected '(' after procedure name")
        params = self._parse_param_list()
        self._expect(TokenType.RPAREN, "Expected ')' after parameter list")
        self._expect(TokenType.SEMI, "Expected ';' after procedure header")
        declarations, procedures = self._parse_declare_part()
        body = self._parse_program_body()
        return ast.ProcedureDecl(name.lexeme, params, declarations, procedures, body, keyword.line)

    def _parse_param_list(self) -> list[ast.ParamSpec]:
        params: list[ast.ParamSpec] = []
        if self._check(TokenType.RPAREN):
            return params
        params.extend(self._parse_param_group())
        while self._match(TokenType.SEMI):
            params.extend(self._parse_param_group())
        return params

    def _parse_param_group(self) -> list[ast.ParamSpec]:
        is_ref = self._match(TokenType.VAR)
        if not (self._check(TokenType.INTEGER) or self._check(TokenType.CHAR)):
            raise CompileError("Expected parameter type", self._peek().line)
        type_token = self._advance()
        names = [self._expect(TokenType.ID, "Expected parameter name")]
        while self._match(TokenType.COMMA):
            names.append(self._expect(TokenType.ID, "Expected parameter name"))
        return [ast.ParamSpec(name.lexeme, type_token.lexeme.lower(), is_ref, name.line) for name in names]

    def _parse_statement_list(self, terminators: set[TokenType]) -> list[ast.Statement]:
        statements = [self._parse_statement()]
        while self._match(TokenType.SEMI):
            if self._peek().type in terminators:
                break
            statements.append(self._parse_statement())
        return statements

    def _parse_statement(self) -> ast.Statement:
        token = self._peek()
        if token.type == TokenType.ID:
            if self._check_next(TokenType.LPAREN):
                return self._parse_call()
            return self._parse_assign()
        if token.type == TokenType.READ:
            return self._parse_read()
        if token.type == TokenType.WRITE:
            return self._parse_write()
        if token.type == TokenType.RETURN:
            return self._parse_return()
        if token.type == TokenType.IF:
            return self._parse_if()
        if token.type == TokenType.WHILE:
            return self._parse_while()
        raise CompileError(f"Unexpected token '{token.lexeme}'", token.line)

    def _parse_assign(self) -> ast.AssignStmt:
        target = self._parse_reference("Expected assignment target")
        self._expect(TokenType.ASSIGN, "Expected ':=' in assignment")
        value = self._parse_expr()
        return ast.AssignStmt(target, value, target.line)

    def _parse_read(self) -> ast.ReadStmt:
        keyword = self._advance()
        self._expect(TokenType.LPAREN, "Expected '(' after read")
        target = self._parse_reference("Expected identifier in read")
        self._expect(TokenType.RPAREN, "Expected ')' after read argument")
        return ast.ReadStmt(target, keyword.line)

    def _parse_write(self) -> ast.WriteStmt:
        keyword = self._advance()
        self._expect(TokenType.LPAREN, "Expected '(' after write")
        value = self._parse_expr()
        self._expect(TokenType.RPAREN, "Expected ')' after write argument")
        return ast.WriteStmt(value, keyword.line)

    def _parse_call(self) -> ast.CallStmt:
        name = self._expect(TokenType.ID, "Expected procedure name")
        self._expect(TokenType.LPAREN, "Expected '(' after procedure name")
        args: list[ast.Expression] = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_expr())
            while self._match(TokenType.COMMA):
                args.append(self._parse_expr())
        self._expect(TokenType.RPAREN, "Expected ')' after call arguments")
        return ast.CallStmt(name.lexeme, args, name.line)

    def _parse_return(self) -> ast.ReturnStmt:
        keyword = self._advance()
        self._expect(TokenType.LPAREN, "Expected '(' after return")
        value = self._parse_expr()
        self._expect(TokenType.RPAREN, "Expected ')' after return value")
        return ast.ReturnStmt(value, keyword.line)

    def _parse_if(self) -> ast.IfStmt:
        keyword = self._advance()
        condition = self._parse_condition()
        self._expect(TokenType.THEN, "Expected 'then'")
        then_body = self._parse_statement_list({TokenType.ELSE})
        self._expect(TokenType.ELSE, "Expected 'else'")
        else_body = self._parse_statement_list({TokenType.FI})
        self._expect(TokenType.FI, "Expected 'fi'")
        return ast.IfStmt(condition, then_body, else_body, keyword.line)

    def _parse_while(self) -> ast.WhileStmt:
        keyword = self._advance()
        condition = self._parse_condition()
        self._expect(TokenType.DO, "Expected 'do'")
        body = self._parse_statement_list({TokenType.ENDWH})
        self._expect(TokenType.ENDWH, "Expected 'endwh'")
        return ast.WhileStmt(condition, body, keyword.line)

    def _parse_condition(self) -> ast.Condition:
        left = self._parse_expr()
        operator = self._advance()
        if operator.type not in {TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NEQ}:
            raise CompileError("Expected relational operator", operator.line)
        right = self._parse_expr()
        return ast.Condition(left, operator.lexeme, right, operator.line)

    def _parse_expr(self) -> ast.Expression:
        expr = self._parse_term()
        while self._match(TokenType.PLUS) or self._match(TokenType.MINUS):
            operator = self._previous()
            right = self._parse_term()
            expr = ast.BinaryExpr(expr, operator.lexeme, right, operator.line)
        return expr

    def _parse_term(self) -> ast.Expression:
        expr = self._parse_unary()
        while self._match(TokenType.TIMES) or self._match(TokenType.DIVIDE):
            operator = self._previous()
            right = self._parse_unary()
            expr = ast.BinaryExpr(expr, operator.lexeme, right, operator.line)
        return expr

    def _parse_unary(self) -> ast.Expression:
        if self._match(TokenType.MINUS):
            operator = self._previous()
            return ast.UnaryExpr(operator.lexeme, self._parse_unary(), operator.line)
        return self._parse_factor()

    def _parse_factor(self) -> ast.Expression:
        token = self._peek()
        if self._match(TokenType.INTC):
            return ast.IntLiteral(int(token.lexeme), token.line)
        if self._match(TokenType.CHARC):
            return ast.CharLiteral(ord(token.lexeme), repr(token.lexeme), token.line)
        if self._match(TokenType.STRINGC):
            return ast.StringLiteral(token.lexeme, token.line)
        if self._check(TokenType.ID):
            return self._parse_reference("Expected identifier")
        if self._match(TokenType.LPAREN):
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        raise CompileError(f"Unexpected factor '{token.lexeme}'", token.line)

    def _parse_reference(self, message: str) -> ast.Reference:
        token = self._expect(TokenType.ID, message)
        ref: ast.Reference = ast.VarRef(token.lexeme, token.line)
        if self._match(TokenType.LBRACK):
            index = self._parse_expr()
            self._expect(TokenType.RBRACK, "Expected ']' after array index")
            ref = ast.ArrayRef(token.lexeme, index, token.line)
        return ref

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self.current += 1
            return True
        return False

    def _expect(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            self.current += 1
            return self.tokens[self.current - 1]
        raise CompileError(message, self._peek().line)

    def _check(self, token_type: TokenType) -> bool:
        return self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def _advance(self) -> Token:
        token = self._peek()
        self.current += 1
        return token

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
