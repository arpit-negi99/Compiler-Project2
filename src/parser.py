"""
parser.py — Algo2Code Section 1
Recursive-descent parser that converts a flat token stream (from the Lexer)
into a typed Abstract Syntax Tree built from ast_nodes classes.

Grammar (informal BNF):
  program     := statement*
  statement   := read | print | assign | for | if | while
  read        := READ IDENTIFIER
  print       := PRINT expr
  assign      := SET IDENTIFIER = expr
  for         := FOR IDENTIFIER = expr TO expr statement* END
  if          := IF condition statement* [ELSE statement*] END
  while       := WHILE condition statement* END
  condition   := expr (CMP_OP expr)?
  expr        := term (('+' | '-') term)*
  term        := factor (('*' | '/') factor)*
  factor      := NUMBER | IDENTIFIER | '(' expr ')' | '-' factor
"""

from .lexer     import TT, Token
from .ast_nodes import (
    ProgramNode, ReadNode, PrintNode, AssignNode,
    ForNode, IfNode, WhileNode,
    NumberNode, VariableNode, BinaryOpNode, UnaryOpNode, ConditionNode,
)


# ─────────────────────────────────────────────
#  Errors
# ─────────────────────────────────────────────

class ParseError(Exception):
    pass


# Human-readable correction hints  (keyword_ctx, next_token_hint) -> suggestion
SYNTAX_HINTS: dict = {
    "FOR_no_var": (
        "FOR must be followed by a variable name.\n"
        "  Correct:  FOR i = 1 TO n\n"
        "                SET ...\n"
        "            END"
    ),
    "FOR_no_eq": (
        "After \'FOR variable\' you need \'= start TO end\'.\n"
        "  Correct:  FOR i = 1 TO n"
    ),
    "FOR_no_TO": (
        "The start value must be followed by TO and an end value.\n"
        "  Correct:  FOR i = 1 TO n"
    ),
    "SET_no_var": (
        "SET must be followed by a variable name.\n"
        "  Correct:  SET sum = 0"
    ),
    "SET_no_eq": (
        "After \'SET variable\' you need \'= expression\'.\n"
        "  Correct:  SET total = a + b"
    ),
    "READ_no_var": (
        "READ must be followed by a variable name.\n"
        "  Correct:  READ n"
    ),
    "IF_no_cond": (
        "IF must be followed by a condition on the same line.\n"
        "  Correct:  IF x > 0\n"
        "                ...\n"
        "            END"
    ),
    "WHILE_no_cond": (
        "WHILE must be followed by a condition on the same line.\n"
        "  Correct:  WHILE i > 0\n"
        "                ...\n"
        "            END"
    ),
    "PRINT_no_expr": (
        "PRINT must be followed by a variable or expression.\n"
        "  Correct:  PRINT sum"
    ),
    "stmt_needs_keyword": (
        "Every statement must start with a keyword:\n"
        "  READ  SET  PRINT  FOR  IF  WHILE\n"
        "  Did you mean:  SET variable = expression ?"
    ),
    "missing_END": (
        "A FOR / IF / WHILE block must be closed with END on its own line.\n"
        "  Example:\n"
        "    FOR i = 1 TO n\n"
        "        SET sum = sum + i\n"
        "    END"
    ),
}


# ─────────────────────────────────────────────
#  Parser
# ─────────────────────────────────────────────

class Parser:
    """
    Consumes a list of Token objects (as produced by Lexer.tokenize()) and
    returns a ProgramNode AST on success, or raises ParseError.
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos    = 0

    # ── token helpers ────────────────────────

    @property
    def _cur(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, *types: TT) -> Token:
        """Consume and return the current token, asserting its type."""
        tok = self._cur
        if tok.type not in types:
            type_names = ', '.join(t.name for t in types)
            raise ParseError(
                f"Line {tok.line}: expected {type_names} "
                f"but got {tok.type.name} ({tok.value!r})"
            )
        return self._advance()

    def _expect_keyword(self, keyword: str) -> Token:
        tok = self._cur
        if tok.type != TT.KEYWORD or tok.value != keyword:
            raise ParseError(
                f"Line {tok.line}: expected keyword '{keyword}' "
                f"but got {tok.type.name} ({tok.value!r})"
            )
        return self._advance()

    def _skip_newlines(self):
        while self._cur.type == TT.NEWLINE:
            self._advance()

    def _is_keyword(self, *keywords: str) -> bool:
        tok = self._cur
        return tok.type == TT.KEYWORD and tok.value in keywords

    # ── public entry point ───────────────────

    def parse(self) -> ProgramNode:
        """Parse the full program and return its AST."""
        self._skip_newlines()
        stmts = self._parse_statement_list(stop_on=set())
        self._expect(TT.EOF)
        return ProgramNode(stmts)

    # ── statement list ───────────────────────

    def _parse_statement_list(self, stop_on: set) -> list:
        """
        Parse zero-or-more statements, stopping when we see:
          • EOF
          • a keyword in `stop_on`  (e.g. END, ELSE)
        """
        stmts = []
        while True:
            self._skip_newlines()
            tok = self._cur
            if tok.type == TT.EOF:
                break
            if tok.type == TT.KEYWORD and tok.value in stop_on:
                break
            stmt = self._parse_one_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    # ── individual statements ─────────────────

    def _hint(self, key: str) -> str:
        h = SYNTAX_HINTS.get(key, "")
        return ("\n\n  Hint:\n    " + h.replace("\n", "\n    ")) if h else ""

    def _parse_one_statement(self):
        self._skip_newlines()
        tok = self._cur

        if tok.type == TT.IDENTIFIER:
            raise ParseError(
                f"Line {tok.line}: unexpected identifier {tok.value!r} at start of statement."
                + self._hint("stmt_needs_keyword")
            )

        if tok.type != TT.KEYWORD:
            raise ParseError(
                f"Line {tok.line}: statement must start with a keyword "
                f"(READ, SET, PRINT, FOR, IF, WHILE), "
                f"got {tok.type.name} ({tok.value!r})"
            )

        dispatch = {
            'READ':  self._parse_read,
            'PRINT': self._parse_print,
            'SET':   self._parse_assign,
            'FOR':   self._parse_for,
            'IF':    self._parse_if,
            'WHILE': self._parse_while,
        }

        if tok.value not in dispatch:
            raise ParseError(
                f"Line {tok.line}: unexpected keyword '{tok.value}' — "
                f"END and ELSE are block-closers, not standalone statements."
            )

        return dispatch[tok.value]()

    # ── READ ─────────────────────────────────

    def _parse_read(self) -> ReadNode:
        self._expect_keyword('READ')
        if self._cur.type != TT.IDENTIFIER:
            raise ParseError(
                f"Line {self._cur.line}: READ must be followed by a variable name, "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("READ_no_var")
            )
        name = self._advance().value
        return ReadNode(name)

    # ── PRINT ────────────────────────────────

    def _parse_print(self) -> PrintNode:
        self._expect_keyword('PRINT')
        if self._cur.type in (TT.NEWLINE, TT.EOF):
            raise ParseError(
                f"Line {self._cur.line}: PRINT needs a variable or expression."
                + self._hint("PRINT_no_expr")
            )
        expr = self._parse_expr()
        return PrintNode(expr)

    # ── SET (assignment) ──────────────────────

    def _parse_assign(self) -> AssignNode:
        self._expect_keyword('SET')
        if self._cur.type != TT.IDENTIFIER:
            raise ParseError(
                f"Line {self._cur.line}: SET must be followed by a variable name, "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("SET_no_var")
            )
        name = self._advance().value
        if self._cur.type != TT.EQUALS:
            raise ParseError(
                f"Line {self._cur.line}: expected '=' after 'SET {name}', "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("SET_no_eq")
            )
        self._advance()   # consume '='
        expr = self._parse_expr()
        return AssignNode(name, expr)

    # ── FOR loop ─────────────────────────────

    def _parse_for(self) -> ForNode:
        self._expect_keyword('FOR')
        if self._cur.type != TT.IDENTIFIER:
            raise ParseError(
                f"Line {self._cur.line}: FOR must be followed by a variable name, "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("FOR_no_var")
            )
        var = self._advance().value
        if self._cur.type != TT.EQUALS:
            raise ParseError(
                f"Line {self._cur.line}: expected '= start TO end' after 'FOR {var}', "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("FOR_no_eq")
            )
        self._advance()   # consume '='
        start = self._parse_expr()
        if not (self._cur.type == TT.KEYWORD and self._cur.value == 'TO'):
            raise ParseError(
                f"Line {self._cur.line}: expected keyword 'TO' after start value, "
                f"got {self._cur.type.name} ({self._cur.value!r})."
                + self._hint("FOR_no_TO")
            )
        self._advance()   # consume 'TO'
        end = self._parse_expr()
        body = self._parse_statement_list(stop_on={'END'})
        if not (self._cur.type == TT.KEYWORD and self._cur.value == 'END'):
            raise ParseError(
                f"Line {self._cur.line}: FOR block starting with 'FOR {var}' "
                f"was never closed — expected END."
                + self._hint("missing_END")
            )
        self._advance()   # consume 'END'
        return ForNode(var, start, end, body)

    # ── IF / ELSE ────────────────────────────

    def _parse_if(self) -> IfNode:
        self._expect_keyword('IF')
        if self._cur.type in (TT.NEWLINE, TT.EOF):
            raise ParseError(
                f"Line {self._cur.line}: IF needs a condition on the same line."
                + self._hint("IF_no_cond")
            )
        cond = self._parse_condition()
        body = self._parse_statement_list(stop_on={'END', 'ELSE'})

        else_body = None
        if self._is_keyword('ELSE'):
            self._advance()
            else_body = self._parse_statement_list(stop_on={'END'})

        if not (self._cur.type == TT.KEYWORD and self._cur.value == 'END'):
            raise ParseError(
                f"Line {self._cur.line}: IF block was never closed — expected END."
                + self._hint("missing_END")
            )
        self._advance()   # consume 'END'
        return IfNode(cond, body, else_body)

    # ── WHILE loop ───────────────────────────

    def _parse_while(self) -> WhileNode:
        self._expect_keyword('WHILE')
        if self._cur.type in (TT.NEWLINE, TT.EOF):
            raise ParseError(
                f"Line {self._cur.line}: WHILE needs a condition on the same line."
                + self._hint("WHILE_no_cond")
            )
        cond = self._parse_condition()
        body = self._parse_statement_list(stop_on={'END'})
        if not (self._cur.type == TT.KEYWORD and self._cur.value == 'END'):
            raise ParseError(
                f"Line {self._cur.line}: WHILE block was never closed — expected END."
                + self._hint("missing_END")
            )
        self._advance()   # consume 'END'
        return WhileNode(cond, body)

    # ── condition ────────────────────────────

    def _parse_condition(self):
        """
        condition := expr (CMP_OP expr)?
        If no comparison operator follows, the expression is used as a
        truthy/falsy boolean directly.
        """
        left = self._parse_expr()
        if self._cur.type == TT.COMPARISON:
            op    = self._advance().value
            right = self._parse_expr()
            return ConditionNode(left, op, right)
        return left     # bare expression used as bool

    # ── expressions (precedence climbing) ────

    def _parse_expr(self):
        """expr := term (('+' | '-') term)*"""
        left = self._parse_term()
        while self._cur.type in (TT.PLUS, TT.MINUS):
            op    = self._advance().value
            right = self._parse_term()
            left  = BinaryOpNode(left, op, right)
        return left

    def _parse_term(self):
        """term := factor (('*' | '/' | '%') factor)*"""
        left = self._parse_factor()
        while self._cur.type in (TT.MULTIPLY, TT.DIVIDE, TT.MODULO):
            op    = self._advance().value
            right = self._parse_factor()
            left  = BinaryOpNode(left, op, right)
        return left

    def _parse_factor(self):
        """factor := NUMBER | IDENTIFIER | '(' expr ')' | '-' factor"""
        tok = self._cur

        if tok.type == TT.INTEGER:
            self._advance()
            return NumberNode(tok.value)

        if tok.type == TT.FLOAT:
            self._advance()
            return NumberNode(tok.value)

        if tok.type == TT.IDENTIFIER:
            self._advance()
            return VariableNode(tok.value)

        if tok.type == TT.LPAREN:
            self._advance()             # consume '('
            expr = self._parse_expr()
            self._expect(TT.RPAREN)
            return expr

        if tok.type == TT.MINUS:
            self._advance()             # consume '-'
            operand = self._parse_factor()
            return UnaryOpNode('-', operand)

        raise ParseError(
            f"Line {tok.line}: unexpected token in expression: "
            f"{tok.type.name} ({tok.value!r})"
        )