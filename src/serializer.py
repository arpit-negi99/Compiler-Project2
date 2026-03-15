"""
serializer.py — Algo2Code Section 1
Converts the AST and interpreter result into a JSON-serialisable dict.
This dict is the formal output contract that Section 2 (Code Generator) reads.

Section 2 should call:
    from serializer import serialize_result, load_result
    data = load_result("section1_output.json")
"""

import json
from .ast_nodes import (
    ProgramNode, ReadNode, PrintNode, AssignNode,
    ForNode, IfNode, WhileNode,
    NumberNode, VariableNode, BinaryOpNode, UnaryOpNode, ConditionNode,
)


# ─────────────────────────────────────────────
#  AST → dict
# ─────────────────────────────────────────────

def _expr_node_to_dict(node) -> dict:
    if isinstance(node, NumberNode):
        return {"type": "Number", "value": node.value}
    if isinstance(node, VariableNode):
        return {"type": "Variable", "name": node.name}
    if isinstance(node, UnaryOpNode):
        return {"type": "UnaryOp", "op": node.op,
                "operand": _expr_node_to_dict(node.operand)}
    if isinstance(node, BinaryOpNode):
        return {"type": "BinaryOp", "op": node.op,
                "left":  _expr_node_to_dict(node.left),
                "right": _expr_node_to_dict(node.right)}
    if isinstance(node, ConditionNode):
        return {"type": "Condition", "op": node.op,
                "left":  _expr_node_to_dict(node.left),
                "right": _expr_node_to_dict(node.right)}
    return {"type": "Unknown", "repr": repr(node)}


def _stmt_node_to_dict(node) -> dict:
    if isinstance(node, ReadNode):
        return {"type": "Read", "variable": node.variable}

    if isinstance(node, PrintNode):
        return {"type": "Print",
                "expression": _expr_node_to_dict(node.expression)}

    if isinstance(node, AssignNode):
        return {"type": "Assign",
                "variable":   node.variable,
                "expression": _expr_node_to_dict(node.expression)}

    if isinstance(node, ForNode):
        return {"type":       "For",
                "variable":   node.variable,
                "start":      _expr_node_to_dict(node.start_expr),
                "end":        _expr_node_to_dict(node.end_expr),
                "body":       [_stmt_node_to_dict(s) for s in node.body],
                "direction":  getattr(node, 'direction', None)}

    if isinstance(node, IfNode):
        d = {"type":      "If",
             "condition": _expr_node_to_dict(node.condition),
             "body":      [_stmt_node_to_dict(s) for s in node.body],
             "else_body": None}
        if node.else_body:
            d["else_body"] = [_stmt_node_to_dict(s) for s in node.else_body]
        return d

    if isinstance(node, WhileNode):
        return {"type":      "While",
                "condition": _expr_node_to_dict(node.condition),
                "body":      [_stmt_node_to_dict(s) for s in node.body]}

    return {"type": "Unknown", "repr": repr(node)}


def ast_to_dict(program: ProgramNode) -> dict:
    """Convert a full ProgramNode AST into a JSON-serialisable dict."""
    return {
        "type":       "Program",
        "statements": [_stmt_node_to_dict(s) for s in program.statements],
    }


# ─────────────────────────────────────────────
#  Full result serialisation
# ─────────────────────────────────────────────

def serialize_result(program: ProgramNode,
                     execution_result: dict,
                     source_code: str = "") -> dict:
    """
    Build the complete Section 1 output payload.

    Args:
        program:          the parsed ProgramNode AST
        execution_result: dict from Interpreter.execution_result
        source_code:      original pseudo-code string (optional, for reference)

    Returns:
        A JSON-serialisable dict — the contract for Section 2.
    """
    return {
        "algo2code_section": 1,
        "source_code":       source_code,
        "ast":               ast_to_dict(program),
        "simulation":        execution_result,
    }


def save_result(payload: dict, filepath: str):
    """Write the serialised result to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)


def load_result(filepath: str) -> dict:
    """Load a previously saved Section 1 result (entry point for Section 2)."""
    with open(filepath, 'r', encoding='utf-8') as fh:
        return json.load(fh)
