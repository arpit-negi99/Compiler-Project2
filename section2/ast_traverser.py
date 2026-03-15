# ==============================================================
#   Algo2Code Compiler - Section 2
#   File: ast_traverser.py
#
#   Recursively walks the AST and applies translation rules from
#   RuleEngine to produce properly indented target-language lines.
#
#   Key features
#   ------------
#   • Variable-declaration tracking for C++:
#       – ReadNode  → int var;  (already in the rule template)
#       – First AssignNode for a var → int {var} = {expr};
#       – Subsequent AssignNodes    → {var} = {expr};
#   • Blank-line insertion:
#       – Python : blank lines only around BLOCK statements
#       – C++    : blank line between every top-level statement
#   • Nested blocks with correct indentation
# ==============================================================

from expression_converter import ExpressionConverter

_BLOCK_TYPES = {'For', 'While', 'If', 'IfElse'}


class ASTTraverser:

    def __init__(self, rule_engine):
        self.re   = rule_engine
        self.expr = ExpressionConverter()

        self.indent_size  = int(self.re.get_config('INDENT_SIZE', 4))
        self.language     = self.re.get_config('LANGUAGE', 'python').lower()

        # Variables declared so far (C++ only).
        # ReadNode marks its var declared; first AssignNode emits 'int var = …'
        self._declared: set = set()

    # ----------------------------------------------------------
    # Public entry point
    # ----------------------------------------------------------

    def traverse(self, node, level: int = 0) -> list:
        if node is None:
            return []
        dispatch = {
            'Program' : self._program,
            'Read'    : self._read,
            'Print'   : self._print,
            'Assign'  : self._assign,
            'For'     : self._for,
            'While'   : self._while,
            'If'      : self._if,
            'IfElse'  : self._if_else,
            'BinaryOp': self._binary_op,
            'UnaryOp' : self._unary_op,
            'Number'  : self._number,
            'Variable': self._variable,
            'Condition': self._condition,
        }
        handler = dispatch.get(node.get('type', ''), self._unknown)
        return handler(node, level)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _ind(self, level: int) -> str:
        return ' ' * (self.indent_size * level)

    def _apply(self, rule: dict, subs: dict,
               section: str = 'open_lines', level: int = 0) -> list:
        out = []
        for tmpl in rule.get(section, []):
            line = tmpl
            for k, v in subs.items():
                line = line.replace('{' + k + '}', str(v))
            out.append(self._ind(level) + line)
        return out

    def _body(self, children: list, level: int) -> list:
        out = []
        for child in children:
            out.extend(self.traverse(child, level))
        return out

    def _e(self, node) -> str:
        return self.expr.convert(node)

    # ----------------------------------------------------------
    # ProgramNode – handles blank-line policy
    # ----------------------------------------------------------

    def _program(self, node, level: int) -> list:
        body  = node.get('statements', [])
        lines = []

        for idx, child in enumerate(body):
            ctype = child.get('type', '')
            ptype = body[idx - 1].get('type', '') if idx > 0 else ''

            if idx > 0:
                if self.language == 'cpp':
                    # Blank line between every top-level statement in C++
                    lines.append('')
                else:
                    # Python: blank only around block statements
                    if ctype in _BLOCK_TYPES or ptype in _BLOCK_TYPES:
                        lines.append('')

            lines.extend(self.traverse(child, level))

        return lines

    # ----------------------------------------------------------
    # Leaf statements
    # ----------------------------------------------------------

    def _read(self, node, level: int) -> list:
        rule = self.re.get_rule('Read')
        if not rule:
            return [self._ind(level) + '# [missing rule: Read]']
        var = node.get('variable', '')
        self._declared.add(var)          # ReadNode declares its variable
        return self._apply(rule, {'var': var}, level=level)

    def _print(self, node, level: int) -> list:
        rule = self.re.get_rule('Print')
        if not rule:
            return [self._ind(level) + '# [missing rule: Print]']
        return self._apply(rule, {'expr': self._e(node.get('expression'))}, level=level)

    def _assign(self, node, level: int) -> list:
        rule = self.re.get_rule('Assign')
        if not rule:
            return [self._ind(level) + '# [missing rule: Assign]']

        var      = node.get('variable', '')
        expr_str = self._e(node.get('expression'))

        # C++ first assignment → emit  int var = expr;
        if self.language == 'cpp' and var not in self._declared:
            self._declared.add(var)
            subs = {'var': f'int {var}', 'expr': expr_str}
        else:
            subs = {'var': var, 'expr': expr_str}

        return self._apply(rule, subs, level=level)

    # ----------------------------------------------------------
    # Block statements
    # ----------------------------------------------------------

    def _for(self, node, level: int) -> list:
        # Choose rule based on direction
        direction = node.get('direction', 'forward')
        rule_name = 'ForReverse' if direction == 'reverse' else 'For'
        rule = self.re.get_rule(rule_name)
        if not rule:
            return [self._ind(level) + f'# [missing rule: {rule_name}]']
        
        # The for-loop variable is declared by the rule (int {var} = …)
        self._declared.add(node.get('variable', ''))
        subs = {
            'var'  : node.get('variable', 'i'),
            'start': self._e(node.get('start')),
            'end'  : self._e(node.get('end')),
        }
        return self._emit_block(rule, subs, node.get('body', []), level)

    def _while(self, node, level: int) -> list:
        rule = self.re.get_rule('While')
        if not rule:
            return [self._ind(level) + '# [missing rule: While]']
        subs = {'condition': self._e(node.get('condition'))}
        return self._emit_block(rule, subs, node.get('body', []), level)

    def _if(self, node, level: int) -> list:
        rule = self.re.get_rule('If')
        if not rule:
            return [self._ind(level) + '# [missing rule: If]']
        subs  = {'condition': self._e(node.get('condition'))}
        tbody = node.get('then_body', node.get('body', []))
        return self._emit_block(rule, subs, tbody, level)

    def _if_else(self, node, level: int) -> list:
        rule = self.re.get_rule('IfElse')
        if not rule:
            return [self._ind(level) + '# [missing rule: IfElse]']
        subs  = {'condition': self._e(node.get('condition'))}
        tbody = node.get('then_body', [])
        ebody = node.get('else_body', [])
        lines  = self._apply(rule, subs, 'open_lines',  level=level)
        lines += self._body(tbody, level + 1)
        lines += self._apply(rule, subs, 'else_lines',  level=level)
        lines += self._body(ebody, level + 1)
        lines += self._apply(rule, subs, 'close_lines', level=level)
        return lines

    def _unknown(self, node, level: int) -> list:
        return [self._ind(level) + f'# [unhandled: {node.get("type","?")}]']

    # ----------------------------------------------------------
    # Expression handlers
    # ----------------------------------------------------------

    def _binary_op(self, node, level: int) -> list:
        rule = self.engine.get_rule('BinaryOp')
        subs = {
            'left': self._e(node.get('left')),
            'op': node.get('op', ''),
            'right': self._e(node.get('right')),
        }
        return self._apply(rule, subs, 'open_lines', level=level)

    def _unary_op(self, node, level: int) -> list:
        rule = self.engine.get_rule('UnaryOp')
        subs = {
            'op': node.get('op', ''),
            'operand': self._e(node.get('operand')),
        }
        return self._apply(rule, subs, 'open_lines', level=level)

    def _number(self, node, level: int) -> list:
        rule = self.engine.get_rule('Number')
        subs = {'value': node.get('value', '')}
        return self._apply(rule, subs, 'open_lines', level=level)

    def _variable(self, node, level: int) -> list:
        rule = self.engine.get_rule('Variable')
        subs = {'name': node.get('name', '')}
        return self._apply(rule, subs, 'open_lines', level=level)

    def _condition(self, node, level: int) -> list:
        rule = self.engine.get_rule('Condition')
        subs = {
            'left': self._e(node.get('left')),
            'op': node.get('op', ''),
            'right': self._e(node.get('right')),
        }
        return self._apply(rule, subs, 'open_lines', level=level)

    # ----------------------------------------------------------
    # Generic BLOCK emitter
    # ----------------------------------------------------------

    def _emit_block(self, rule: dict, subs: dict,
                    children: list, level: int) -> list:
        lines  = self._apply(rule, subs, 'open_lines',  level=level)
        lines += self._body(children, level + 1)
        lines += self._apply(rule, subs, 'close_lines', level=level)
        return lines
