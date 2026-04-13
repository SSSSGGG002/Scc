from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snlc.compiler import compile_file
from snlc.errors import CompileError
from snlc.runtime import run_mips


def _decode_run_input(value: str | None) -> str | None:
    if value is None:
        return None
    return bytes(value, "utf-8").decode("unicode_escape")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a small SNL subset to MIPS using quadruples.")
    parser.add_argument("source", help="Path to the SNL source file")
    parser.add_argument("-o", "--output", help="Path to the generated MIPS file")
    parser.add_argument("--ir-out", help="Optional path to write quadruples")
    parser.add_argument("--tokens-out", help="Optional path to write token stream")
    parser.add_argument("--ast-out", help="Optional path to write the syntax tree")
    parser.add_argument("--run", action="store_true", help="Run the generated MIPS program with MARS")
    parser.add_argument("--mars-jar", help="Path to the MARS jar file")
    parser.add_argument("--run-input", help="Optional stdin content to feed into the MIPS program")
    args = parser.parse_args()

    try:
        result = compile_file(args.source)
    except CompileError as exc:
        print(exc, file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else Path(args.source).with_suffix(".asm")
    output_path.write_text(result.mips, encoding="utf-8")

    if args.ir_out:
        Path(args.ir_out).write_text(result.format_quads() + "\n", encoding="utf-8")
    if args.tokens_out:
        Path(args.tokens_out).write_text(result.format_tokens() + "\n", encoding="utf-8")
    if args.ast_out:
        Path(args.ast_out).write_text(result.format_ast() + "\n", encoding="utf-8")

    print(f"MIPS written to {output_path}")
    print("Syntax tree:")
    print(result.format_ast())
    print("Quadruples:")
    print(result.format_quads())

    if args.run:
        try:
            runtime = run_mips(
                output_path,
                mars_jar=args.mars_jar,
                stdin_data=_decode_run_input(args.run_input),
            )
        except FileNotFoundError as exc:
            print(exc, file=sys.stderr)
            return 1
        if runtime.stdout:
            print("Program output:")
            sys.stdout.write(runtime.stdout)
            if not runtime.stdout.endswith("\n"):
                print()
        if runtime.stderr:
            print(runtime.stderr, file=sys.stderr, end="" if runtime.stderr.endswith("\n") else "\n")
        if runtime.exit_code != 0:
            return runtime.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
