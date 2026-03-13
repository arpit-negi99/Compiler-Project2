"""
ast_nodes.py — Algo2Code Section 1
Defines all AST node classes used by the Parser and Interpreter.
Each node class represents a single syntactic construct in the pseudo-code language.
"""


# ─────────────────────────────────────────────
#  Expression Nodes
# ─────────────────────────────────────────────

class NumberNode:
    """A literal integer or float value."""
    def __init__(self, value):
        self.value = value          # int | float

    def __repr__(self):
        return f"Number({self.value})"


class VariableNode:
    """A reference to a named variable."""
    def __init__(self, name):
        self.name = name            # str

    def __repr__(self):
        return f"Var({self.name})"


class BinaryOpNode:
    """A binary arithmetic operation: left OP right."""
    def __init__(self, left, op, right):
        self.left  = left           # ExprNode
        self.op    = op             # '+' | '-' | '*' | '/'
        self.right = right          # ExprNode

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOpNode:
    """A unary operation (currently only unary minus)."""
    def __init__(self, op, operand):
        self.op      = op           # '-'
        self.operand = operand      # ExprNode

    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"


class ConditionNode:
    """A boolean comparison: left CMP right."""
    VALID_OPS = ('==', '!=', '<', '>', '<=', '>=')

    def __init__(self, left, op, right):
        self.left  = left           # ExprNode
        self.op    = op             # one of VALID_OPS
        self.right = right          # ExprNode

    def __repr__(self):
        return f"Condition({self.left} {self.op} {self.right})"


# ─────────────────────────────────────────────
#  Statement Nodes
# ─────────────────────────────────────────────

class ProgramNode:
    """Root of the AST — holds a list of top-level statements."""
    def __init__(self, statements):
        self.statements = statements    # list[StmtNode]

    def __repr__(self):
        return f"Program([{len(self.statements)} statement(s)])"


class ReadNode:
    """READ variable — request a value from the user at runtime."""
    def __init__(self, variable):
        self.variable = variable    # str

    def __repr__(self):
        return f"Read({self.variable})"


class PrintNode:
    """PRINT expression — output the value of an expression."""
    def __init__(self, expression):
        self.expression = expression    # ExprNode

    def __repr__(self):
        return f"Print({self.expression})"


class AssignNode:
    """SET variable = expression — assign a computed value to a variable."""
    def __init__(self, variable, expression):
        self.variable   = variable      # str
        self.expression = expression    # ExprNode

    def __repr__(self):
        return f"Assign({self.variable} = {self.expression})"


class ForNode:
    """FOR variable = start TO end … END — counted iteration."""
    def __init__(self, variable, start_expr, end_expr, body):
        self.variable   = variable      # str
        self.start_expr = start_expr    # ExprNode
        self.end_expr   = end_expr      # ExprNode
        self.body       = body          # list[StmtNode]

    def __repr__(self):
        return (f"For({self.variable} = {self.start_expr} TO "
                f"{self.end_expr}, [{len(self.body)} stmt(s)])")


class IfNode:
    """IF condition … [ELSE …] END — conditional branching."""
    def __init__(self, condition, body, else_body=None):
        self.condition = condition      # ConditionNode | ExprNode
        self.body      = body           # list[StmtNode]
        self.else_body = else_body      # list[StmtNode] | None

    def __repr__(self):
        has_else = self.else_body is not None
        return (f"If({self.condition}, then=[{len(self.body)} stmt(s)]"
                + (f", else=[{len(self.else_body)} stmt(s)]" if has_else else "") + ")")


class WhileNode:
    """WHILE condition … END — pre-condition loop."""
    def __init__(self, condition, body):
        self.condition = condition      # ConditionNode | ExprNode
        self.body      = body           # list[StmtNode]

    def __repr__(self):
        return f"While({self.condition}, [{len(self.body)} stmt(s)])"
