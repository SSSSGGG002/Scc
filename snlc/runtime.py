from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


DEFAULT_MARS_JAR = "Mars for Compile 2022.jar"


@dataclass
class RuntimeResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str


def resolve_mars_jar(mars_jar: str | Path | None = None) -> Path:
    if mars_jar is not None:
        jar_path = Path(mars_jar)
    else:
        jar_path = Path.cwd() / DEFAULT_MARS_JAR
    if not jar_path.exists():
        raise FileNotFoundError(f"MARS jar not found: {jar_path}")
    return jar_path


def run_mips(
    asm_path: str | Path,
    mars_jar: str | Path | None = None,
    stdin_data: str | None = None,
) -> RuntimeResult:
    asm_file = Path(asm_path)
    jar_path = resolve_mars_jar(mars_jar)
    command = ["java", "-jar", str(jar_path), "nc", "sm", str(asm_file)]
    completed = subprocess.run(
        command,
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )
    return RuntimeResult(command, completed.returncode, completed.stdout, completed.stderr)
