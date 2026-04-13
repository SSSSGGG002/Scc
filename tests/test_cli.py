from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_cli_can_compile_and_run_hello(tmp_path: Path) -> None:
    output_path = tmp_path / "hello.asm"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            str(ROOT / "examples" / "hello.snl"),
            "-o",
            str(output_path),
            "--run",
            "--mars-jar",
            str(ROOT / "Mars for Compile 2022.jar"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert output_path.exists()
    assert "MIPS written to" in completed.stdout
    assert "Program output:" in completed.stdout
    assert "Hello" in completed.stdout


def test_cli_can_run_advanced_example(tmp_path: Path) -> None:
    output_path = tmp_path / "advanced.asm"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            str(ROOT / "examples" / "advanced.snl"),
            "-o",
            str(output_path),
            "--run",
            "--mars-jar",
            str(ROOT / "Mars for Compile 2022.jar"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "folded" in completed.stdout
    assert "\n7\n10\n" in completed.stdout


def test_cli_can_run_array_example(tmp_path: Path) -> None:
    output_path = tmp_path / "arrays.asm"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            str(ROOT / "examples" / "arrays.snl"),
            "-o",
            str(output_path),
            "--run",
            "--mars-jar",
            str(ROOT / "Mars for Compile 2022.jar"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "\n24\n" in completed.stdout


def test_cli_can_run_procedure_example(tmp_path: Path) -> None:
    output_path = tmp_path / "procedures.asm"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            str(ROOT / "examples" / "procedures.snl"),
            "-o",
            str(output_path),
            "--run",
            "--mars-jar",
            str(ROOT / "Mars for Compile 2022.jar"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "\n5\n" in completed.stdout


def test_cli_can_write_ast_output(tmp_path: Path) -> None:
    output_path = tmp_path / "hello.asm"
    ast_path = tmp_path / "hello.ast"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            str(ROOT / "examples" / "hello.snl"),
            "-o",
            str(output_path),
            "--ast-out",
            str(ast_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert ast_path.exists()
    ast_text = ast_path.read_text(encoding="utf-8")
    assert "Program hello" in ast_text
    assert "Write" in ast_text
    assert "Syntax tree:" in completed.stdout
