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

_BLOCK_TYPES = {'ForNode', 'WhileNode', 'IfNode', 'IfElseNode'}


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
            'ProgramNode' : self._program,
            'ReadNode'    : self._read,
            'PrintNode'   : self._print,
            'AssignNode'  : self._assign,
            'ForNode'     : self._for,
            'WhileNode'   : self._while,
            'IfNode'      : self._if,
            'IfElseNode'  : self._if_else,
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
        body  = node.get('body', [])
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
        rule = self.re.get_rule('ReadNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: ReadNode]']
        var = node.get('var', '')
        self._declared.add(var)          # ReadNode declares its variable
        return self._apply(rule, {'var': var}, level=level)

    def _print(self, node, level: int) -> list:
        rule = self.re.get_rule('PrintNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: PrintNode]']
        return self._apply(rule, {'expr': self._e(node.get('expr'))}, level=level)

    def _assign(self, node, level: int) -> list:
        rule = self.re.get_rule('AssignNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: AssignNode]']

        var      = node.get('var', '')
        expr_str = self._e(node.get('expr'))

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
        rule = self.re.get_rule('ForNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: ForNode]']
        # The for-loop variable is declared by the rule (int {var} = …)
        self._declared.add(node.get('var', ''))
        subs = {
            'var'  : node.get('var', 'i'),
            'start': self._e(node.get('start')),
            'end'  : self._e(node.get('end')),
        }
        return self._emit_block(rule, subs, node.get('body', []), level)

    def _while(self, node, level: int) -> list:
        rule = self.re.get_rule('WhileNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: WhileNode]']
        subs = {'condition': self._e(node.get('condition'))}
        return self._emit_block(rule, subs, node.get('body', []), level)

    def _if(self, node, level: int) -> list:
        rule = self.re.get_rule('IfNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: IfNode]']
        subs  = {'condition': self._e(node.get('condition'))}
        tbody = node.get('then_body', node.get('body', []))
        return self._emit_block(rule, subs, tbody, level)

    def _if_else(self, node, level: int) -> list:
        rule = self.re.get_rule('IfElseNode')
        if not rule:
            return [self._ind(level) + '# [missing rule: IfElseNode]']
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
    # Generic BLOCK emitter
    # ----------------------------------------------------------

    def _emit_block(self, rule: dict, subs: dict,
                    children: list, level: int) -> list:
        lines  = self._apply(rule, subs, 'open_lines',  level=level)
        lines += self._body(children, level + 1)
        lines += self._apply(rule, subs, 'close_lines', level=level)
        return lines
