"""
ast_printer.py — Algo2Code Section 1
Pretty-prints the AST in a readable tree format for the result preview.
Keeps all rendering logic separate from the AST node definitions.
"""

from .ast_nodes import (
    ProgramNode, ReadNode, PrintNode, AssignNode,
    ForNode, IfNode, WhileNode,
    NumberNode, VariableNode, BinaryOpNode, UnaryOpNode, ConditionNode,
)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _expr_to_str(node) -> str:
    """Convert an expression node to a compact infix string."""
    if isinstance(node, NumberNode):
        return str(node.value)
    if isinstance(node, VariableNode):
        return node.name
    if isinstance(node, UnaryOpNode):
        return f"-{_expr_to_str(node.operand)}"
    if isinstance(node, BinaryOpNode):
        return (f"({_expr_to_str(node.left)} "
                f"{node.op} "
                f"{_expr_to_str(node.right)})")
    if isinstance(node, ConditionNode):
        return (f"{_expr_to_str(node.left)} "
                f"{node.op} "
                f"{_expr_to_str(node.right)}")
    return repr(node)


# ─────────────────────────────────────────────
#  Main printer
# ─────────────────────────────────────────────

class ASTPrinter:
    """
    Produces a multi-line tree string for a ProgramNode.

    Example output:
        Program
        ├── Read(n)
        ├── Assign(sum = 0)
        ├── For(i = 1 TO n)
        │   └── Assign(sum = (sum + i))
        └── Print(sum)
    """

    def render(self, program: ProgramNode) -> str:
        lines = ["Program"]
        self._render_stmts(program.statements, lines, prefix="")
        return "\n".join(lines)

    def _render_stmts(self, stmts: list, lines: list, prefix: str):
        for idx, stmt in enumerate(stmts):
            is_last   = (idx == len(stmts) - 1)
            connector = "└── " if is_last else "├── "
            child_pfx = prefix + ("    " if is_last else "│   ")
            self._render_node(stmt, lines, prefix + connector, child_pfx)

    def _render_node(self, node, lines: list, connector: str, child_pfx: str):
        if isinstance(node, ReadNode):
            lines.append(f"{connector}Read({node.variable})")

        elif isinstance(node, PrintNode):
            lines.append(f"{connector}Print({_expr_to_str(node.expression)})")

        elif isinstance(node, AssignNode):
            lines.append(
                f"{connector}Assign({node.variable} = "
                f"{_expr_to_str(node.expression)})"
            )

        elif isinstance(node, ForNode):
            lines.append(
                f"{connector}For({node.variable} = "
                f"{_expr_to_str(node.start_expr)} TO "
                f"{_expr_to_str(node.end_expr)})"
            )
            self._render_stmts(node.body, lines, child_pfx)

        elif isinstance(node, IfNode):
            cond_str = _expr_to_str(node.condition)
            lines.append(f"{connector}If({cond_str})")
            # then-branch
            then_label = "│   then" if node.else_body else "    then"
            lines.append(f"{child_pfx}then:")
            self._render_stmts(node.body, lines, child_pfx + "  ")
            if node.else_body:
                lines.append(f"{child_pfx}else:")
                self._render_stmts(node.else_body, lines, child_pfx + "  ")

        elif isinstance(node, WhileNode):
            cond_str = _expr_to_str(node.condition)
            lines.append(f"{connector}While({cond_str})")
            self._render_stmts(node.body, lines, child_pfx)

        else:
            lines.append(f"{connector}{repr(node)}")


# ─────────────────────────────────────────────
#  Convenience function
# ─────────────────────────────────────────────

def print_ast(program: ProgramNode) -> None:
    """Print the full AST tree to stdout."""
    printer = ASTPrinter()
    print(printer.render(program))


def ast_to_string(program: ProgramNode) -> str:
    """Return the full AST tree as a string (for logging / export)."""
    return ASTPrinter().render(program)
