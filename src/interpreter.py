"""
interpreter.py — Algo2Code Section 1
Tree-walking interpreter that executes the AST produced by the Parser.

Key design decisions:
  • Variables are stored in a flat dict (support_scope can be added in Section 2).
  • PRINT results are collected in a list so the result-preview layer can
    display them after execution.
  • The interpreter is intentionally stateless between runs; call reset()
    to reuse the same instance for a fresh execution.
  • The final `execution_result` dict is the contract exported to Section 2.
"""

from .ast_nodes import (
    ProgramNode, ReadNode, PrintNode, AssignNode,
    ForNode, IfNode, WhileNode,
    NumberNode, VariableNode, BinaryOpNode, UnaryOpNode, ConditionNode,
)


# ─────────────────────────────────────────────
#  Errors
# ─────────────────────────────────────────────

class InterpreterError(Exception):
    pass


# ─────────────────────────────────────────────
#  Interpreter
# ─────────────────────────────────────────────

WHILE_ITER_LIMIT = 100_000   # safety cap to catch infinite loops


class Interpreter:
    """
    Executes a ProgramNode AST.

    Usage:
        interp = Interpreter()
        interp.set_inputs({"n": 5, "m": 3})
        interp.execute(ast)
        result = interp.execution_result   # dict ready for Section 2
    """

    def __init__(self):
        self.variables: dict  = {}      # variable store
        self.outputs:   list  = []      # collected PRINT values (in order)
        self._inputs:   dict  = {}      # values for READ statements
        self._read_order: list = []     # tracks which vars were READ and when

    # ── configuration ────────────────────────

    def reset(self):
        """Clear all state so the interpreter can be reused."""
        self.variables.clear()
        self.outputs.clear()
        self._read_order.clear()

    def set_inputs(self, inputs: dict):
        """
        Provide a mapping of {variable_name: value} for all READ statements.
        Values should already be the correct Python numeric type (int / float).
        """
        self._inputs = {k: v for k, v in inputs.items()}

    # ── public entry point ───────────────────

    def execute(self, program: ProgramNode):
        """Run the full program. Raises InterpreterError on any runtime fault."""
        self._exec_stmts(program.statements)

    # ── statement dispatch ───────────────────

    def _exec_stmts(self, stmts: list):
        for stmt in stmts:
            self._exec_one(stmt)

    def _exec_one(self, stmt):
        dispatch = {
            ReadNode:   self._exec_read,
            PrintNode:  self._exec_print,
            AssignNode: self._exec_assign,
            ForNode:    self._exec_for,
            IfNode:     self._exec_if,
            WhileNode:  self._exec_while,
        }
        handler = dispatch.get(type(stmt))
        if handler is None:
            raise InterpreterError(f"Unknown statement type: {type(stmt).__name__}")
        handler(stmt)

    # ── statement executors ──────────────────

    def _exec_read(self, node: ReadNode):
        var = node.variable
        if var not in self._inputs:
            raise InterpreterError(
                f"READ '{var}': no input value was provided for this variable."
            )
        value = self._inputs[var]
        # Coerce to numeric if stored as string
        if isinstance(value, str):
            try:
                value = float(value) if '.' in value else int(value)
            except ValueError:
                pass        # keep as string
        self.variables[var] = value
        self._read_order.append(var)

    def _exec_print(self, node: PrintNode):
        value = self._eval_expr(node.expression)
        # Format: keep int-looking floats clean
        if isinstance(value, float) and value == int(value):
            value = int(value)
        self.outputs.append(value)

    def _exec_assign(self, node: AssignNode):
        value = self._eval_expr(node.expression)
        self.variables[node.variable] = value

    def _exec_for(self, node: ForNode):
        start = int(self._eval_expr(node.start_expr))
        end   = int(self._eval_expr(node.end_expr))
        step  = 1 if start <= end else -1
        
        # Set direction in AST node for code generation
        node.direction = 'forward' if step > 0 else 'reverse'
        
        for i in range(start, end + step, step):
            self.variables[node.variable] = i
            self._exec_stmts(node.body)

    def _exec_if(self, node: IfNode):
        if self._eval_cond(node.condition):
            self._exec_stmts(node.body)
        elif node.else_body:
            self._exec_stmts(node.else_body)

    def _exec_while(self, node: WhileNode):
        iterations = 0
        while self._eval_cond(node.condition):
            self._exec_stmts(node.body)
            iterations += 1
            if iterations > WHILE_ITER_LIMIT:
                raise InterpreterError(
                    f"WHILE loop exceeded {WHILE_ITER_LIMIT:,} iterations "
                    "(possible infinite loop — check your condition)."
                )

    # ── expression evaluator ─────────────────

    def _eval_expr(self, node):
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, VariableNode):
            if node.name not in self.variables:
                raise InterpreterError(
                    f"Variable '{node.name}' is used before being defined."
                )
            return self.variables[node.name]

        if isinstance(node, UnaryOpNode):
            val = self._eval_expr(node.operand)
            if node.op == '-':
                return -val
            raise InterpreterError(f"Unknown unary operator: {node.op!r}")

        if isinstance(node, BinaryOpNode):
            left  = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            op    = node.op
            if op == '+':
                return left + right
            if op == '-':
                return left - right
            if op == '*':
                return left * right
            if op == '/':
                if right == 0:
                    raise InterpreterError("Division by zero.")
                result = left / right
                # Return int when division is exact
                return int(result) if result == int(result) else result
            if op == '%':
                if right == 0:
                    raise InterpreterError("Modulo by zero.")
                result = left % right
                return int(result) if isinstance(result, float) and result == int(result) else result
            raise InterpreterError(f"Unknown binary operator: {op!r}")

        raise InterpreterError(f"Unknown expression node: {type(node).__name__}")

    # ── condition evaluator ──────────────────

    def _eval_cond(self, node) -> bool:
        if isinstance(node, ConditionNode):
            left  = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            ops = {
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
                '<':  lambda a, b: a <  b,
                '>':  lambda a, b: a >  b,
                '<=': lambda a, b: a <= b,
                '>=': lambda a, b: a >= b,
            }
            if node.op not in ops:
                raise InterpreterError(f"Unknown comparison operator: {node.op!r}")
            return ops[node.op](left, right)

        # Bare expression used as bool (e.g. WHILE x)
        return bool(self._eval_expr(node))

    # ── result export (contract for Section 2) ──

    @property
    def execution_result(self) -> dict:
        """
        Returns a serialisable dict that Section 2 (Code Generator) will consume.
        Structure is stable — add fields but never remove them.
        """
        return {
            "section": 1,
            "status": "success",
            "inputs":    dict(self._inputs),
            "outputs":   list(self.outputs),
            "variables": dict(self.variables),
            "read_order": list(self._read_order),
        }
