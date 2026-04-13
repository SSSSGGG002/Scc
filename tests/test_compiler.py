from __future__ import annotations

import pytest

from snlc.compiler import compile_file, compile_source
from snlc.errors import CompileError


def test_compile_string_literal_to_ir_and_mips() -> None:
    result = compile_source(
        """
program hello
begin
  write("Hello")
end.
""".strip()
    )

    assert result.string_literals == {"s1": "Hello"}
    assert "(write, s1, string, _)" in result.format_quads()
    assert 'str_s1: .asciiz "Hello"' in result.mips
    assert "Program hello" in result.format_ast()
    assert "Write" in result.format_ast()


def test_demo_program_still_compiles() -> None:
    result = compile_file("examples/demo.snl")

    assert result.quadruples
    assert "main:" in result.mips


def test_unary_minus_and_relational_operators_compile() -> None:
    result = compile_source(
        """
program ops
var
  integer x;
begin
  x := -(1 + 2) * 3;
  if x <= -9 then
    write("ok")
  else
    write("bad")
  fi
end.
""".strip()
    )

    quads = result.format_quads()
    assert "(assign, -9, _, x)" in quads
    assert "(bgt, x, -9, L1)" in quads
    assert 'str_s1: .asciiz "ok"' in result.mips


def test_array_declaration_and_indexed_access_compile() -> None:
    result = compile_source(
        """
program arrays
var
  integer nums[4], i;
begin
  nums[0] := 3;
  i := nums[0];
  write(i)
end.
""".strip()
    )

    assert result.symbols["nums"].size == 4
    quads = result.format_quads()
    assert "(assign, 3, _, nums[0])" in quads
    assert "(assign, nums[0], _, i)" in quads
    assert "sym_nums: .space 16" in result.mips
    assert "runtime_bounds_error:" in result.mips
    assert "bounds_error_msg: .asciiz" in result.mips


def test_constant_condition_folds_to_unconditional_goto() -> None:
    result = compile_source(
        """
program foldcond
begin
  if 2 > 3 then
    write("bad")
  else
    write("ok")
  fi
end.
""".strip()
    )

    quads = result.format_quads()
    assert "(goto, _, _, L1)" in quads
    assert "ble" not in quads


def test_procedure_call_with_nested_scope_compiles() -> None:
    result = compile_source(
        """
program procedures
var
  integer x;
procedure bump(integer step; var integer target);
  procedure twice();
  begin
    target := target + step
  end
begin
  twice();
  twice()
end
begin
  x := 1;
  bump(2, x);
  write(x)
end.
""".strip()
    )

    quads = result.format_quads()
    assert "(param, 2, _, bump__step)" in quads
    assert "(param_ref, &x, _, bump__target)" in quads
    assert "(call, _, _, bump__twice)" in quads
    assert "ptr_bump__step: .word 0" in result.mips
    assert "jal proc_bump" in result.mips


def test_recursive_procedure_with_reference_parameter_compiles() -> None:
    result = compile_source(
        """
program recurse
var
  integer x;
procedure dec(var integer n);
begin
  if n = 0 then
    write(0)
  else
    n := n - 1;
    dec(n)
  fi
end
begin
  x := 2;
  dec(x);
  write(x)
end.
""".strip()
    )

    quads = result.format_quads()
    assert "(param_ref, &dec__n, _, dec__n)" in quads
    assert "(call, _, _, dec)" in quads
    assert "proc_dec:" in result.mips
    assert "end_proc_dec:" in result.mips


def test_ast_text_output_contains_hierarchy() -> None:
    result = compile_source(
        """
program astdemo
var
  integer x;
procedure bump(integer n; var integer y);
begin
  y := y + n
end
begin
  x := 1;
  bump(2, x);
  write(x)
end.
""".strip()
    )

    tree = result.format_ast()
    assert "Program astdemo" in tree
    assert "Procedure bump" in tree
    assert "Param value integer n" in tree
    assert "Param ref integer y" in tree
    assert "Call bump" in tree
    assert "Binary +" in tree


def test_division_by_zero_in_constant_expression_is_compile_error() -> None:
    with pytest.raises(CompileError, match="Division by zero in constant expression"):
        compile_source(
            """
program divzero
var
  integer x;
begin
  x := 1 / (3 - 3)
end.
""".strip()
        )


def test_array_literal_index_out_of_bounds_is_compile_error() -> None:
    with pytest.raises(CompileError, match="Array index 4 out of bounds"):
        compile_source(
            """
program badindex
var
  integer nums[4];
begin
  nums[4] := 1
end.
""".strip()
        )


def test_array_must_be_indexed_before_use() -> None:
    with pytest.raises(CompileError, match="Array 'nums' must be indexed before use"):
        compile_source(
            """
program baduse
var
  integer nums[2], x;
begin
  x := nums
end.
""".strip()
        )


def test_string_values_are_rejected_in_conditions() -> None:
    with pytest.raises(CompileError, match="String values can only be used with write\\(\\)"):
        compile_source(
            """
program bad
begin
  if "x" = "x" then
    write(1)
  else
    write(0)
  fi
end.
""".strip()
        )
