# ==============================================================
#   Algo2Code Compiler - Section 2
#   File: expression_converter.py
#
#   Converts expression AST nodes into string representations.
#
#   Supported node types
#   --------------------
#   NumberNode   – integer / float literal
#   VariableNode – identifier reference
#   BinaryOpNode – left op right  (+, -, *, /, %, <, >, ==, !=,
#                                   <=, >=, &&, ||, and, or)
#   UnaryOpNode  – op operand  (-, not)
#   StringNode   – quoted string literal
#   BoolNode     – true / false
# ==============================================================


class ExpressionConverter:
    """
    Recursive expression-node-to-string converter.

    Call  .convert(node)  at the top level; it strips unnecessary
    outer parentheses from the final result.
    """

    # Operators that need child sub-expressions parenthesised when
    # the child is also a BinaryOpNode (precedence safety).
    _LOW_PREC = {'+', '-', '<', '>', '<=', '>=', '==', '!=',
                 '&&', '||', 'and', 'or'}

    def convert(self, node, top_level: bool = True) -> str:
        """Public entry point.  Strips outer parens at the top level."""
        result = self._visit(node)
        if top_level:
            result = self._strip_outer_parens(result)
        return result

    # ----------------------------------------------------------
    # Internal visitor
    # ----------------------------------------------------------

    def _visit(self, node) -> str:
        if node is None:
            return ''

        ntype = node.get('type', '')

        if ntype == 'Number':
            val = node.get('value', 0)
            # Represent integer-valued floats without the decimal point
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            return str(val)

        if ntype == 'Variable':
            return node.get('name', '')

        if ntype == 'String':
            return f'"{node.get("value", "")}"'

        if ntype == 'Bool':
            return 'true' if node.get('value', True) else 'false'

        if ntype == 'UnaryOp':
            op      = node.get('op', '-')
            operand = self._visit(node['operand'])
            return f'{op}{operand}'

        if ntype == 'BinaryOp':
            return self._binary(node)

        # Comparison node variant (some AST serialisers use this)
        if ntype == 'CompareNode':
            left  = self._visit(node['left'])
            right = self._visit(node['right'])
            op    = node.get('op', '==')
            return f'{left} {op} {right}'

        # Fallback – return value or name if present
        if 'value' in node:
            return str(node['value'])
        if 'name' in node:
            return node['name']
        return ''

    def _binary(self, node) -> str:
        op    = node.get('op', '+')
        left  = self._visit(node['left'])
        right = self._visit(node['right'])

        # Parenthesise child BinaryOpNode for low-precedence operators
        if node['left'].get('type') == 'BinaryOpNode' and op in self._LOW_PREC:
            left = f'({left})'
        if node['right'].get('type') == 'BinaryOpNode' and op in self._LOW_PREC:
            right = f'({right})'

        return f'{left} {op} {right}'

    # ----------------------------------------------------------
    # Helper: strip outer parens only if they span the whole string
    # ----------------------------------------------------------

    @staticmethod
    def _strip_outer_parens(s: str) -> str:
        if len(s) < 2 or s[0] != '(' or s[-1] != ')':
            return s
        depth = 0
        for i, ch in enumerate(s):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            # If depth hits 0 before the last character the outer
            # parens do NOT span the whole expression.
            if depth == 0 and i < len(s) - 1:
                return s
        return s[1:-1]
