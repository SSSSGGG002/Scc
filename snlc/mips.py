from __future__ import annotations

from .ir import AddressOf, ArrayAccess, Quadruple
from .semantics import ProcedureSymbol, SemanticInfo, Symbol


class MIPSGenerator:
    def __init__(
        self,
        semantic_info: SemanticInfo,
        temp_types: dict[str, str],
        quads: list[Quadruple],
        string_literals: dict[str, str],
    ) -> None:
        self.global_symbols = semantic_info.globals
        self.symbols = semantic_info.all_symbols
        self.procedures = semantic_info.procedures
        self.temp_types = temp_types
        self.quads = quads
        self.string_literals = string_literals
        self.has_arrays = any(symbol.size is not None for symbol in self.symbols.values())
        self.lines: list[str] = []

    def generate(self) -> str:
        self.lines = [
            ".data",
            "newline: .asciiz \"\\n\"",
        ]
        if self.has_arrays:
            self.lines.append("bounds_error_msg: .asciiz \"Array index out of bounds\\n\"")

        for name, value in self.string_literals.items():
            self.lines.append(f"{self._string_label(name)}: .asciiz \"{self._escape_string(value)}\"")
        if self.symbols or self.temp_types:
            self.lines.append(".align 2")
        for symbol in self.symbols.values():
            self._declare_symbol(symbol)
        for proc in self.procedures.values():
            for param in proc.params:
                self.lines.append(f"{self._arg_label(param.storage_name)}: .word 0")
        for name in self.temp_types:
            self.lines.append(f"{self._label(name)}: .word 0")

        main_quads, proc_quads = self._split_quads()
        self.lines.extend(
            [
                "",
                ".text",
                ".globl main",
                "main:",
            ]
        )
        for quad in main_quads:
            self.lines.append(f"    # {quad}")
            self._emit_quad(quad)

        self.lines.extend(
            [
                "    li $v0, 10",
                "    syscall",
            ]
        )
        if proc_quads:
            self.lines.append("")
            for quad in proc_quads:
                if quad.op in {"proc", "endproc"}:
                    self.lines.append(f"    # {quad}")
                else:
                    self.lines.append(f"    # {quad}")
                self._emit_quad(quad)
        if self.has_arrays:
            self.lines.extend(
                [
                    "",
                    f"{self._bounds_error_label()}:",
                    "    la $a0, bounds_error_msg",
                    "    li $v0, 4",
                    "    syscall",
                    "    li $v0, 10",
                    "    syscall",
                ]
            )
        return "\n".join(self.lines) + "\n"

    def _split_quads(self) -> tuple[list[Quadruple], list[Quadruple]]:
        for index, quad in enumerate(self.quads):
            if quad.op == "proc":
                return self.quads[:index], self.quads[index:]
        return self.quads, []

    def _declare_symbol(self, symbol: Symbol) -> None:
        if symbol.owner_proc is None:
            if symbol.size is None:
                self.lines.append(f"{self._label(symbol.storage_name)}: .word 0")
            else:
                self.lines.append(f"{self._label(symbol.storage_name)}: .space {symbol.size * 4}")
            return

        self.lines.append(f"{self._ptr_label(symbol.storage_name)}: .word 0")

    def _emit_quad(self, quad: Quadruple) -> None:
        op = quad.op
        if op == "label":
            self.lines.append(f"{quad.result}:")
            return
        if op == "goto":
            self.lines.append(f"    j {quad.result}")
            return
        if op == "proc":
            self._emit_proc_prologue(str(quad.result))
            return
        if op == "endproc":
            self._emit_proc_epilogue(str(quad.result))
            return
        if op == "return":
            self.lines.append(f"    j {self._proc_end_label(str(quad.result))}")
            return
        if op == "call":
            self.lines.append(f"    jal {self._proc_label(str(quad.result))}")
            return
        if op == "param":
            self._load_operand(quad.arg1, "$t0")
            self.lines.append(f"    sw $t0, {self._arg_label(str(quad.result))}")
            return
        if op == "param_ref":
            self._load_address_operand(quad.arg1, "$t0")
            self.lines.append(f"    sw $t0, {self._arg_label(str(quad.result))}")
            return
        if op == "assign":
            self._load_operand(quad.arg1, "$t0")
            self._store_target(quad.result, "$t0")
            return
        if op in {"add", "sub", "mul"}:
            self._load_operand(quad.arg1, "$t0")
            self._load_operand(quad.arg2, "$t1")
            inst = {"add": "add", "sub": "sub", "mul": "mul"}[op]
            self.lines.append(f"    {inst} $t2, $t0, $t1")
            self.lines.append(f"    sw $t2, {self._label(str(quad.result))}")
            return
        if op == "div":
            self._load_operand(quad.arg1, "$t0")
            self._load_operand(quad.arg2, "$t1")
            self.lines.append("    div $t0, $t1")
            self.lines.append("    mflo $t2")
            self.lines.append(f"    sw $t2, {self._label(str(quad.result))}")
            return
        if op == "read":
            if quad.arg1 == "char":
                self.lines.append("    li $v0, 12")
            else:
                self.lines.append("    li $v0, 5")
            self.lines.append("    syscall")
            self._store_target(quad.result, "$v0")
            return
        if op == "write":
            if quad.arg2 == "string":
                self.lines.append(f"    la $a0, {self._string_label(str(quad.arg1))}")
                self.lines.append("    li $v0, 4")
            else:
                self._load_operand(quad.arg1, "$a0")
                if quad.arg2 == "char":
                    self.lines.append("    li $v0, 11")
                else:
                    self.lines.append("    li $v0, 1")
            self.lines.append("    syscall")
            self.lines.append("    la $a0, newline")
            self.lines.append("    li $v0, 4")
            self.lines.append("    syscall")
            return
        if op in {"bge", "bgt", "ble", "blt", "bne", "beq"}:
            self._load_operand(quad.arg1, "$t0")
            self._load_operand(quad.arg2, "$t1")
            self.lines.append(f"    {op} $t0, $t1, {quad.result}")
            return
        raise ValueError(f"Unsupported quadruple op '{op}'")

    def _emit_proc_prologue(self, qualified_name: str) -> None:
        proc = self.procedures[qualified_name]
        frame_symbols = proc.locals
        frame_size = 4 + len(frame_symbols) * 4 + sum(self._storage_bytes(symbol) for symbol in frame_symbols if not symbol.is_ref)
        self.lines.append(f"{self._proc_label(qualified_name)}:")
        self.lines.append(f"    addi $sp, $sp, -{frame_size}")
        self.lines.append("    sw $ra, 0($sp)")

        cursor = 4
        storage_cursor = 4 + len(frame_symbols) * 4
        for symbol in frame_symbols:
            self.lines.append(f"    lw $t0, {self._ptr_label(symbol.storage_name)}")
            self.lines.append(f"    sw $t0, {cursor}($sp)")
            if symbol.is_ref:
                self.lines.append(f"    lw $t1, {self._arg_label(symbol.storage_name)}")
                self.lines.append(f"    sw $t1, {self._ptr_label(symbol.storage_name)}")
            else:
                self.lines.append(f"    addi $t1, $sp, {storage_cursor}")
                self.lines.append(f"    sw $t1, {self._ptr_label(symbol.storage_name)}")
                if symbol.is_param:
                    self.lines.append(f"    lw $t2, {self._arg_label(symbol.storage_name)}")
                    self.lines.append("    sw $t2, 0($t1)")
            cursor += 4
            storage_cursor += self._storage_bytes(symbol)

    def _emit_proc_epilogue(self, qualified_name: str) -> None:
        proc = self.procedures[qualified_name]
        frame_symbols = proc.locals
        frame_size = 4 + len(frame_symbols) * 4 + sum(self._storage_bytes(symbol) for symbol in frame_symbols if not symbol.is_ref)
        self.lines.append(f"{self._proc_end_label(qualified_name)}:")
        cursor = 4
        for symbol in frame_symbols:
            self.lines.append(f"    lw $t0, {cursor}($sp)")
            self.lines.append(f"    sw $t0, {self._ptr_label(symbol.storage_name)}")
            cursor += 4
        self.lines.append("    lw $ra, 0($sp)")
        self.lines.append(f"    addi $sp, $sp, {frame_size}")
        self.lines.append("    jr $ra")

    def _load_operand(self, operand: object, register: str) -> None:
        if isinstance(operand, int):
            self.lines.append(f"    li {register}, {operand}")
            return
        if isinstance(operand, ArrayAccess):
            self._load_array_address(operand, "$t9", "$t8")
            self.lines.append(f"    lw {register}, 0($t9)")
            return
        symbol = self.symbols.get(str(operand))
        if symbol is not None and symbol.owner_proc is not None:
            self.lines.append(f"    lw $t9, {self._ptr_label(symbol.storage_name)}")
            self.lines.append(f"    lw {register}, 0($t9)")
            return
        self.lines.append(f"    lw {register}, {self._label(str(operand))}")

    def _store_target(self, target: object, register: str) -> None:
        if isinstance(target, ArrayAccess):
            self._load_array_address(target, "$t9", "$t8")
            self.lines.append(f"    sw {register}, 0($t9)")
            return
        symbol = self.symbols.get(str(target))
        if symbol is not None and symbol.owner_proc is not None:
            self.lines.append(f"    lw $t9, {self._ptr_label(symbol.storage_name)}")
            self.lines.append(f"    sw {register}, 0($t9)")
            return
        self.lines.append(f"    sw {register}, {self._label(str(target))}")

    def _load_address_operand(self, operand: object, register: str) -> None:
        if not isinstance(operand, AddressOf):
            raise TypeError(f"Expected address operand, got {type(operand)!r}")
        target = operand.target
        if isinstance(target, ArrayAccess):
            self._load_array_address(target, register, "$t8")
            return
        symbol = self.symbols.get(str(target))
        if symbol is not None and symbol.owner_proc is not None:
            self.lines.append(f"    lw {register}, {self._ptr_label(symbol.storage_name)}")
            return
        self.lines.append(f"    la {register}, {self._label(str(target))}")

    def _load_array_address(self, access: ArrayAccess, addr_register: str, index_register: str) -> None:
        self._load_operand(access.index, index_register)
        self.lines.append(f"    bltz {index_register}, {self._bounds_error_label()}")
        self.lines.append(f"    li $t7, {self.symbols[access.name].size}")
        self.lines.append(f"    bge {index_register}, $t7, {self._bounds_error_label()}")
        self.lines.append(f"    sll {index_register}, {index_register}, 2")
        symbol = self.symbols[access.name]
        if symbol.owner_proc is None:
            self.lines.append(f"    la {addr_register}, {self._label(access.name)}")
        else:
            self.lines.append(f"    lw {addr_register}, {self._ptr_label(access.name)}")
        self.lines.append(f"    add {addr_register}, {addr_register}, {index_register}")

    def _storage_bytes(self, symbol: Symbol) -> int:
        if symbol.size is None:
            return 4
        return symbol.size * 4

    def _label(self, name: str) -> str:
        return f"sym_{name}"

    def _ptr_label(self, name: str) -> str:
        return f"ptr_{name}"

    def _arg_label(self, name: str) -> str:
        return f"arg_{name}"

    def _string_label(self, name: str) -> str:
        return f"str_{name}"

    def _proc_label(self, name: str) -> str:
        return f"proc_{name}"

    def _proc_end_label(self, name: str) -> str:
        return f"end_{self._proc_label(name)}"

    def _bounds_error_label(self) -> str:
        return "runtime_bounds_error"

    def _escape_string(self, value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
