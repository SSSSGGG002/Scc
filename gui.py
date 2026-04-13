from __future__ import annotations

import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from snlc.compiler import CompilationResult, compile_source
from snlc.errors import CompileError
from snlc.runtime import resolve_mars_jar, run_mips


ROOT = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT / "examples"
EDITOR_FONT = ("Menlo", 12)
VIEW_FONT = ("Menlo", 11)


def decode_run_input(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")


class CompilerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SNL Compiler Demo")
        self.root.geometry("1420x900")
        self.root.minsize(1180, 760)

        self.temp_dir = tempfile.TemporaryDirectory(prefix="snlc_gui_")
        self.current_file: Path | None = None
        self.last_result: CompilationResult | None = None

        self.example_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.run_input_var = tk.StringVar()
        self.mars_jar_var = tk.StringVar(value=self._default_mars_jar())

        self._configure_style()
        self._build_layout()
        self._load_example_names()
        self._load_startup_source()
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _configure_style(self) -> None:
        bg = "#f3efe7"
        panel = "#fbf8f2"
        accent = "#996c36"
        self.root.configure(bg=bg)
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background=bg)
        style.configure("Toolbar.TFrame", background=bg)
        style.configure("Card.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground="#2f2418")
        style.configure("Muted.TLabel", background=bg, foreground="#665746")
        style.configure("TButton", padding=(10, 6))
        style.configure("Accent.TButton", padding=(12, 7), foreground="#ffffff", background=accent)
        style.map(
            "Accent.TButton",
            background=[("active", "#7f5623"), ("pressed", "#6a451c")],
            foreground=[("disabled", "#ece1d0"), ("!disabled", "#ffffff")],
        )
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background="#ddd1bf", foreground="#3a2d22")
        style.map("TNotebook.Tab", background=[("selected", panel)])

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(14, 12))
        toolbar.grid(row=0, column=0, sticky="ew")
        for column in (1, 7):
            toolbar.columnconfigure(column, weight=1)

        ttk.Label(toolbar, text="Example").grid(row=0, column=0, sticky="w")
        self.example_box = ttk.Combobox(toolbar, textvariable=self.example_var, state="readonly", width=18)
        self.example_box.grid(row=0, column=1, sticky="ew", padx=(8, 12))
        ttk.Button(toolbar, text="Load Example", command=self.load_example).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(toolbar, text="Open File", command=self.open_file).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(toolbar, text="Save Source", command=self.save_source).grid(row=0, column=4, padx=(0, 8))
        ttk.Button(toolbar, text="Compile", command=self.compile_current, style="Accent.TButton").grid(row=0, column=5, padx=(0, 8))
        ttk.Button(toolbar, text="Run", command=self.run_current).grid(row=0, column=6)

        ttk.Label(toolbar, text="Run Input").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(toolbar, textvariable=self.run_input_var).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 12), pady=(12, 0))
        ttk.Label(toolbar, text="MARS Jar").grid(row=1, column=3, sticky="w", pady=(12, 0))
        ttk.Entry(toolbar, textvariable=self.mars_jar_var).grid(row=1, column=4, columnspan=3, sticky="ew", padx=(8, 8), pady=(12, 0))
        ttk.Button(toolbar, text="Browse Jar", command=self.choose_mars_jar).grid(row=1, column=7, sticky="e", pady=(12, 0))

        content = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))

        editor_card = ttk.Frame(content, style="Card.TFrame", padding=10)
        editor_card.columnconfigure(0, weight=1)
        editor_card.rowconfigure(1, weight=1)
        content.add(editor_card, weight=3)

        ttk.Label(editor_card, text="Source", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.source_text = self._make_text(editor_card, row=1, column=0, font=EDITOR_FONT)

        right = ttk.Frame(content, style="Card.TFrame", padding=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        content.add(right, weight=4)

        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.tokens_text = self._add_tab("Tokens")
        self.ast_text = self._add_tab("AST")
        self.ir_text = self._add_tab("IR")
        self.mips_text = self._add_tab("MIPS")
        self.output_text = self._add_tab("Program Output")
        self.errors_text = self._add_tab("Messages")

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", style="Muted.TLabel")
        status.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))

    def _make_text(self, parent: ttk.Frame, row: int, column: int, font: tuple[str, int]) -> tk.Text:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(column, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = tk.Text(
            frame,
            wrap="none",
            undo=True,
            font=font,
            bg="#fffdf8",
            fg="#231b12",
            insertbackground="#231b12",
            selectbackground="#d7c3a5",
            relief="flat",
            padx=10,
            pady=10,
        )
        text.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        return text

    def _add_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.notebook, style="Card.TFrame")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = self._make_text(frame, row=0, column=0, font=VIEW_FONT)
        text.configure(state="disabled")
        self.notebook.add(frame, text=title)
        return text

    def _load_example_names(self) -> None:
        examples = sorted(path.name for path in EXAMPLES_DIR.glob("*.snl"))
        self.example_box["values"] = examples
        if examples:
            preferred = "procedures.snl" if "procedures.snl" in examples else examples[0]
            self.example_var.set(preferred)

    def _load_startup_source(self) -> None:
        startup = EXAMPLES_DIR / self.example_var.get() if self.example_var.get() else None
        if startup and startup.exists():
            self._set_source(startup.read_text(encoding="utf-8"))
            self.current_file = startup
            self.status_var.set(f"Loaded {startup.name}")

    def _set_source(self, text: str) -> None:
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", text)

    def _get_source(self) -> str:
        return self.source_text.get("1.0", tk.END).rstrip() + "\n"

    def _default_mars_jar(self) -> str:
        jar = ROOT / "Mars for Compile 2022.jar"
        return str(jar if jar.exists() else Path("Mars for Compile 2022.jar"))

    def _set_view(self, widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _clear_messages(self) -> None:
        self._set_view(self.output_text, "")
        self._set_view(self.errors_text, "")

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open SNL source",
            filetypes=[("SNL Source", "*.snl"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialdir=str(EXAMPLES_DIR),
        )
        if not path:
            return
        file_path = Path(path)
        self._set_source(file_path.read_text(encoding="utf-8"))
        self.current_file = file_path
        self.status_var.set(f"Opened {file_path.name}")

    def save_source(self) -> None:
        default_name = self.current_file.name if self.current_file else "demo.snl"
        path = filedialog.asksaveasfilename(
            title="Save SNL source",
            defaultextension=".snl",
            initialfile=default_name,
            filetypes=[("SNL Source", "*.snl"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialdir=str(self.current_file.parent if self.current_file else EXAMPLES_DIR),
        )
        if not path:
            return
        file_path = Path(path)
        file_path.write_text(self._get_source(), encoding="utf-8")
        self.current_file = file_path
        self.status_var.set(f"Saved {file_path.name}")

    def load_example(self) -> None:
        if not self.example_var.get():
            return
        path = EXAMPLES_DIR / self.example_var.get()
        self._set_source(path.read_text(encoding="utf-8"))
        self.current_file = path
        self.status_var.set(f"Loaded example {path.name}")

    def choose_mars_jar(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose MARS jar",
            filetypes=[("JAR Files", "*.jar"), ("All Files", "*.*")],
            initialdir=str(ROOT),
        )
        if path:
            self.mars_jar_var.set(path)

    def compile_current(self) -> None:
        self._clear_messages()
        try:
            result = compile_source(self._get_source())
        except CompileError as exc:
            self.last_result = None
            self._set_view(self.errors_text, str(exc))
            self.notebook.select(self.errors_text.master)
            self.status_var.set("Compile failed")
            return
        except Exception as exc:
            self.last_result = None
            self._set_view(self.errors_text, f"Unexpected error:\n{exc}")
            self.notebook.select(self.errors_text.master)
            self.status_var.set("Compile failed")
            return

        self.last_result = result
        self._show_result(result)
        self.status_var.set("Compile succeeded")

    def run_current(self) -> None:
        self.compile_current()
        if self.last_result is None:
            return

        try:
            jar_path = resolve_mars_jar(self.mars_jar_var.get() or None)
        except FileNotFoundError as exc:
            self._set_view(self.errors_text, str(exc))
            self.notebook.select(self.errors_text.master)
            self.status_var.set("Run failed")
            return

        asm_path = Path(self.temp_dir.name) / "gui_output.asm"
        asm_path.write_text(self.last_result.mips, encoding="utf-8")

        runtime = run_mips(
            asm_path,
            mars_jar=jar_path,
            stdin_data=decode_run_input(self.run_input_var.get()) if self.run_input_var.get() else None,
        )

        output_parts: list[str] = []
        if runtime.stdout:
            output_parts.append(runtime.stdout)
        if runtime.stderr:
            output_parts.append("[stderr]")
            output_parts.append(runtime.stderr)
        if not output_parts:
            output_parts.append("(no output)")
        self._set_view(self.output_text, "\n".join(part.rstrip("\n") for part in output_parts).strip() + "\n")
        self.notebook.select(self.output_text.master)

        if runtime.exit_code == 0:
            self.status_var.set(f"Run finished via {jar_path.name}")
            self._set_view(self.errors_text, "")
        else:
            self.status_var.set(f"Run failed with exit code {runtime.exit_code}")
            self._set_view(self.errors_text, runtime.stderr or f"Process exited with code {runtime.exit_code}")

    def _show_result(self, result: CompilationResult) -> None:
        self._set_view(self.tokens_text, result.format_tokens() + "\n")
        self._set_view(self.ast_text, result.format_ast() + "\n")
        self._set_view(self.ir_text, result.format_quads() + "\n")
        self._set_view(self.mips_text, result.mips)
        self._set_view(self.output_text, "")
        message = "Compilation succeeded.\n\nArtifacts are ready for inspection."
        if self.current_file is not None:
            message += f"\nCurrent source: {self.current_file}"
        self._set_view(self.errors_text, message + "\n")
        self.notebook.select(self.ast_text.master)

    def _close(self) -> None:
        self.temp_dir.cleanup()
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    CompilerGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
