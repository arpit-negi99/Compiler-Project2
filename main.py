#!/usr/bin/env python3
"""
main.py — Algo2Code Section 1: Algorithm Parser & Simulator
────────────────────────────────────────────────────────────
Entry point.  Orchestrates the full Section 1 pipeline:

  1. Load pseudo-code  (file arg or interactive editor)
  2. Lex  →  token stream
  3. Parse → AST
  4. Collect inputs for every READ variable
  5. Simulate (interpret) the AST
  6. Display execution preview
  7. Export JSON payload for Section 2

Usage:
  python main.py                      # interactive editor
  python main.py examples/sum.algo    # from file
  python main.py examples/sum.algo --no-prompt   # skip Y/N prompt
"""

import sys
import os
import json
import textwrap

# ── allow `python main.py` from the project root ────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from src.lexer       import Lexer, LexerError
from src.parser      import Parser, ParseError
from src.interpreter import Interpreter, InterpreterError
from src.ast_printer import ast_to_string, print_ast
from src.ast_nodes   import ReadNode, ForNode, IfNode, WhileNode
from src.serializer  import serialize_result, save_result


# ─────────────────────────────────────────────────────────────────────────────
#  Constants / config
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_FILE    = "section1_output.json"
DIVIDER_WIDE   = "=" * 62
DIVIDER_NARROW = "─" * 62


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _banner(title: str):
    print(f"\n{DIVIDER_WIDE}")
    print(f"  {title}")
    print(DIVIDER_WIDE)


def _section(title: str):
    print(f"\n{DIVIDER_NARROW}")
    print(f"  {title}")
    print(DIVIDER_NARROW)


def _collect_read_vars(stmts: list) -> list:
    """
    Walk the AST recursively and return an ordered list of every variable
    name that appears in a READ statement (preserving declaration order,
    deduplicating repeated READs of the same variable).
    """
    seen   = set()
    result = []

    def walk(nodes):
        for node in nodes:
            if isinstance(node, ReadNode):
                if node.variable not in seen:
                    seen.add(node.variable)
                    result.append(node.variable)
            for attr in ('body', 'else_body'):
                sub = getattr(node, attr, None)
                if sub:
                    walk(sub)

    walk(stmts)
    return result


def _get_inputs(variables: list) -> dict:
    """Prompt the user for each READ variable and return a typed dict."""
    inputs = {}
    print("\n  This algorithm requires the following input(s):\n")
    for var in variables:
        while True:
            try:
                raw = input(f"    Enter value for  '{var}'  → ").strip()
                if not raw:
                    print("    (value cannot be empty, please try again)")
                    continue
                # Coerce to numeric where possible
                try:
                    inputs[var] = float(raw) if '.' in raw else int(raw)
                except ValueError:
                    inputs[var] = raw       # keep as string
                break
            except (KeyboardInterrupt, EOFError):
                print("\n\n  [Aborted by user]")
                sys.exit(0)
    return inputs


def _load_source(args: list) -> tuple:
    """
    Return (source_text, filename).
    If a filename is given as CLI arg, read it; otherwise open an
    interactive multi-line editor.
    """
    # Filter out flags
    files = [a for a in args if not a.startswith('--')]

    if files:
        path = files[0]
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                return fh.read(), path
        except FileNotFoundError:
            print(f"\n  ERROR: File not found → {path!r}")
            sys.exit(1)

    # Interactive editor
    print("\n  Paste or type your algorithm below.")
    print("  When finished, type  END_ALGO  on its own line and press Enter.\n")
    lines = []
    try:
        while True:
            line = input("  > ")
            if line.strip().upper() == 'END_ALGO':
                break
            lines.append(line)
    except (KeyboardInterrupt, EOFError):
        print("\n\n  [Aborted by user]")
        sys.exit(0)

    return '\n'.join(lines), '<stdin>'


def _format_value(v) -> str:
    """Pretty-print a value: avoid trailing .0 for whole floats."""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def _display_preview(source: str, inputs: dict,
                     interp: Interpreter, read_vars: list):
    """Print the ALGORITHM EXECUTION PREVIEW block."""

    _banner("ALGORITHM EXECUTION PREVIEW")

    # ── source ───────────────────────────────────────────────────────────────
    print("\n  ┌─ Algorithm ─────────────────────────────────────────────────")
    for line in source.strip().splitlines():
        print(f"  │  {line}")
    print("  └─────────────────────────────────────────────────────────────")

    # ── inputs ───────────────────────────────────────────────────────────────
    if inputs:
        print("\n  ● Inputs")
        for var in read_vars:
            if var in inputs:
                print(f"      {var:15s} = {_format_value(inputs[var])}")

    # ── outputs ──────────────────────────────────────────────────────────────
    print("\n  ● Outputs")
    if interp.outputs:
        for idx, val in enumerate(interp.outputs, start=1):
            label = f"    Output #{idx}" if len(interp.outputs) > 1 else "    Result  "
            print(f"  {label}  →  {_format_value(val)}")
    else:
        print("    (algorithm produced no PRINT output)")

    # ── final variable state ──────────────────────────────────────────────────
    print("\n  ● Final variable state")
    if interp.variables:
        for var, val in interp.variables.items():
            print(f"      {var:15s} = {_format_value(val)}")
    else:
        print("    (no variables in scope)")

    print(f"\n{DIVIDER_WIDE}")


# ─────────────────────────────────────────────────────────────────────────────
#  Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run(source: str,
        inputs_override: dict | None = None,
        silent: bool = False) -> dict:
    """
    Full Section 1 pipeline.

    Args:
        source:          pseudo-code string
        inputs_override: skip interactive input prompts (for testing / API use)
        silent:          suppress stdout (for unit tests)

    Returns:
        The serialisable result dict (same content written to OUTPUT_FILE).

    Raises:
        LexerError, ParseError, InterpreterError on failure.
    """

    def log(*a, **kw):
        if not silent:
            print(*a, **kw)

    # ── 1. Lex ───────────────────────────────────────────────────────────────
    if not silent:
        _section("Step 1 · Lexer")
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    log(f"  {len(tokens) - 1} token(s) produced.")

    # ── 2. Parse ─────────────────────────────────────────────────────────────
    if not silent:
        _section("Step 2 · Parser")
    parser  = Parser(tokens)
    program = parser.parse()
    log(f"  {len(program.statements)} top-level statement(s) parsed.")
    log("\n  AST:")
    for line in ast_to_string(program).splitlines():
        log(f"    {line}")

    # ── 3. Collect inputs ────────────────────────────────────────────────────
    read_vars = _collect_read_vars(program.statements)

    if inputs_override is not None:
        inputs = inputs_override
    elif read_vars:
        if not silent:
            _section("Step 3 · Input Collection")
        inputs = _get_inputs(read_vars)
    else:
        inputs = {}

    # ── 4. Simulate ──────────────────────────────────────────────────────────
    if not silent:
        _section("Step 4 · Simulation")
    interp = Interpreter()
    interp.set_inputs(inputs)
    interp.execute(program)
    log("  Simulation completed successfully.")

    # ── 5. Preview ───────────────────────────────────────────────────────────
    if not silent:
        _display_preview(source, inputs, interp, read_vars)

    # ── 6. Export JSON ────────────────────────────────────────────────────────
    payload = serialize_result(program, interp.execution_result, source)
    save_result(payload, OUTPUT_FILE)
    if not silent:
        log(f"\n  Section 1 output saved → {OUTPUT_FILE}")

    return payload


# ─────────────────────────────────────────────────────────────────────────────
#  CLI entry point
# ─────────────────────────────────────────────────────────────────────────────


def _print_syntax_card():
    """Print a compact syntax cheatsheet after any parse/lex error."""
    print("""
  ┌─ Syntax Reference ──────────────────────────────────────────┐
  │  READ  variable                                             │
  │  SET   variable = expression                                │
  │  PRINT variable  (or any expression)                        │
  │                                                             │
  │  FOR variable = startValue TO endValue                      │
  │      SET ...                                                │
  │  END                                                        │
  │                                                             │
  │  IF condition                                               │
  │      ...                                                    │
  │  ELSE          ← optional                                   │
  │      ...                                                    │
  │  END                                                        │
  │                                                             │
  │  WHILE condition                                            │
  │      ...                                                    │
  │  END                                                        │
  │                                                             │
  │  Operators  : + - * / %                                     │
  │  Comparisons: == != < > <= >=                               │
  │  Comments   : # anything after hash is ignored              │
  └─────────────────────────────────────────────────────────────┘""")

def main():
    args         = sys.argv[1:]
    skip_prompt  = '--no-prompt' in args
    args_clean   = [a for a in args if a != '--no-prompt']

    _banner("Algo2Code  ·  Section 1: Algorithm Parser & Simulator")
    print(textwrap.dedent("""\

      Supported keywords:  READ  PRINT  SET  FOR … TO … END
                           IF … [ELSE …] END   WHILE … END
      Operators:  +  -  *  /    Comparisons:  ==  !=  <  >  <=  >=
    """))

    source, filename = _load_source(args_clean)

    if not source.strip():
        print("\n  ERROR: No algorithm provided.")
        sys.exit(1)

    if filename != '<stdin>':
        print(f"\n  Loaded algorithm from: {filename}")

    try:
        payload = run(source)
    except LexerError as e:
        print(f"\n  [LEXER ERROR]  {e}")
        _print_syntax_card()
        sys.exit(1)
    except ParseError as e:
        print(f"\n  [PARSE ERROR]  {e}")
        _print_syntax_card()
        sys.exit(1)
    except InterpreterError as e:
        print(f"\n  [RUNTIME ERROR]  {e}")
        sys.exit(1)

    # ── prompt for Section 2 ─────────────────────────────────────────────────
    if skip_prompt:
        print("\n  [--no-prompt] Skipping code-generation prompt.")
        return

    print()
    try:
        choice = input("  Proceed to code generation? (Y/N): ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        choice = 'N'

    if choice == 'Y':
        print(f"\n  ✔  Section 1 output is ready in '{OUTPUT_FILE}'.")
        print("     Hand this file to Section 2 (Code Generator) to continue.\n")
    else:
        print("\n  Simulation complete. Exiting Algo2Code Section 1.\n")


if __name__ == '__main__':
    main()