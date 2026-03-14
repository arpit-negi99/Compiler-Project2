#!/usr/bin/env python3
# ==============================================================
#   Algo2Code Compiler - Section 2
#   File: main_codegen.py
#
#   Entry point for rule-based code generation.
#
#   Usage
#   -----
#     python section2/main_codegen.py
#     python section2/main_codegen.py --input path/to/ast.json
#     python section2/main_codegen.py --input ast.json --outdir ./out
#     python section2/main_codegen.py --debug
#
#   Reads  : section1_output.json  (AST from Section 1)
#   Writes : generated_python.py
#            generated_cpp.cpp
# ==============================================================

import json
import os
import sys
import argparse

_SECTION2_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to project root, then to section2
_SECTION2_DIR = os.path.join(_SECTION2_DIR, 'section2')
sys.path.insert(0, _SECTION2_DIR)

from rule_engine   import RuleEngine
from ast_traverser import ASTTraverser

_PROJECT_ROOT = os.path.dirname(_SECTION2_DIR)
_RULES_DIR    = os.path.join(_SECTION2_DIR, 'rules')

DEFAULT_INPUT  = os.path.join(_PROJECT_ROOT, 'section1_output.json')
DEFAULT_OUTDIR = _PROJECT_ROOT


# ------------------------------------------------------------------
# Python generator
# ------------------------------------------------------------------

def generate_python(ast_root: dict, rules_dir: str) -> str:
    engine    = RuleEngine(os.path.join(rules_dir, 'python_rules.l'))
    traverser = ASTTraverser(engine)

    body_lines = traverser.traverse(ast_root, level=0)

    # Python has no header/footer
    all_lines = _trim(body_lines)
    return '\n'.join(all_lines) + '\n'


# ------------------------------------------------------------------
# C++ generator
# ------------------------------------------------------------------

def generate_cpp(ast_root: dict, rules_dir: str) -> str:
    engine    = RuleEngine(os.path.join(rules_dir, 'cpp_rules.l'))
    traverser = ASTTraverser(engine)

    # C++ body lives inside main() → indent level 1
    body_lines = traverser.traverse(ast_root, level=1)

    header = engine.get_header()   # e.g. ['#include <iostream>', ..., 'int main(){']
    footer = engine.get_footer()   # e.g. ['return 0;', '}']

    # Indent non-brace footer lines (e.g. "return 0;" → "    return 0;")
    indent  = ' ' * int(engine.get_config('INDENT_SIZE', 4))
    fmt_footer = []
    for line in footer:
        stripped = line.strip()
        if stripped and not stripped.startswith('}'):
            fmt_footer.append(indent + stripped)
        else:
            fmt_footer.append(stripped)

    all_lines = list(header)
    all_lines.append('')                 # blank line after  int main(){
    all_lines.extend(body_lines)
    all_lines.append('')                 # blank line before  return 0;
    all_lines.extend(fmt_footer)

    return '\n'.join(_trim(all_lines)) + '\n'


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _trim(lines: list) -> list:
    """Remove leading and trailing blank lines from a list."""
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()
    return lines


def load_ast(json_path: str) -> dict:
    if not os.path.exists(json_path):
        print(f'[ERROR] Input file not found: {json_path}', file=sys.stderr)
        sys.exit(1)
    with open(json_path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def write_file(content: str, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description='Algo2Code Section 2 – Rule-Based Code Generator')
    ap.add_argument('--input',  default=DEFAULT_INPUT,
                    help='Path to section1_output.json')
    ap.add_argument('--outdir', default=DEFAULT_OUTDIR,
                    help='Output directory for generated files')
    ap.add_argument('--rules',  default=_RULES_DIR,
                    help='Directory with python_rules.l / cpp_rules.l')
    ap.add_argument('--debug',  action='store_true',
                    help='Dump parsed rule tables before generating')
    args = ap.parse_args()

    _banner()

    # ── Load AST ──────────────────────────────────────────────
    print(f'[*] Loading AST  →  {args.input}')
    json_data = load_ast(args.input)
    ast_root = json_data.get('ast', {})
    print(f'[*] Root node    :  {ast_root.get("type", "?")}')

    if args.debug:
        print('\n[DEBUG] Python rule table:')
        RuleEngine(os.path.join(args.rules, 'python_rules.l')).dump()
        print('\n[DEBUG] C++ rule table:')
        RuleEngine(os.path.join(args.rules, 'cpp_rules.l')).dump()

    # ── Generate Python ───────────────────────────────────────
    print('\n[*] Applying python_rules.l  →  generating Python …')
    py_code = generate_python(ast_root, args.rules)
    py_path = os.path.join(args.outdir, 'generated_python.py')
    write_file(py_code, py_path)
    print(f'[+] Written  :  {py_path}')

    # ── Generate C++ ──────────────────────────────────────────
    print('\n[*] Applying cpp_rules.l  →  generating C++ …')
    cpp_code = generate_cpp(ast_root, args.rules)
    cpp_path = os.path.join(args.outdir, 'generated_cpp.cpp')
    write_file(cpp_code, cpp_path)
    print(f'[+] Written  :  {cpp_path}')

    # ── Print results ─────────────────────────────────────────
    _divider('Generated Python  ( generated_python.py )')
    print(py_code)

    _divider('Generated C++  ( generated_cpp.cpp )')
    print(cpp_code)

    _divider('Done – Section 2 complete')


def _banner():
    b = '=' * 60
    print(b)
    print('   Algo2Code – Section 2 : Rule-Based Code Generation')
    print('   Rules engine  :  Lex-style .l rule files')
    print(b)


def _divider(title: str):
    print(f'\n{"─" * 60}')
    print(f'  {title}')
    print('─' * 60)


if __name__ == '__main__':
    main()
