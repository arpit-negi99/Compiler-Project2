"""
lexer.py — Algo2Code Section 1
Converts raw pseudo-code source text into a flat stream of typed tokens.
The parser then consumes this token stream to build the AST.
"""

from enum import Enum, auto


# ─────────────────────────────────────────────
#  Token Types
# ─────────────────────────────────────────────

class TT(Enum):
    """Token type enumeration."""
    KEYWORD    = auto()   # READ PRINT SET FOR TO END IF ELSE WHILE
    IDENTIFIER = auto()   # variable names
    INTEGER    = auto()   # 42
    FLOAT      = auto()   # 3.14
    PLUS       = auto()   # +
    MINUS      = auto()   # -
    MULTIPLY   = auto()   # *
    DIVIDE     = auto()   # /
    EQUALS     = auto()   # =  (assignment)
    COMPARISON = auto()   # == != < > <= >=
    LPAREN     = auto()   # (
    RPAREN     = auto()   # )
    MODULO     = auto()   # %  (remainder)
    NEWLINE    = auto()   # logical line separator
    EOF        = auto()   # end of source


KEYWORDS: frozenset = frozenset({
    'READ', 'PRINT', 'SET',
    'FOR',  'TO',    'END',
    'IF',   'ELSE',  'WHILE',
})


# ─────────────────────────────────────────────
#  Token
# ─────────────────────────────────────────────

class Token:
    __slots__ = ('type', 'value', 'line')

    def __init__(self, type_: TT, value, line: int = 0):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line})"


# ─────────────────────────────────────────────
#  Errors
# ─────────────────────────────────────────────

class LexerError(Exception):
    pass


# ─────────────────────────────────────────────
#  Lexer
# ─────────────────────────────────────────────

class Lexer:
    """
    Single-pass lexer that walks the source character by character.
    Produces a list of Token objects (including a terminal EOF token).
    """

    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1

    # ── helpers ──────────────────────────────

    @property
    def _ch(self):
        """Current character, or None at end of source."""
        return self.source[self.pos] if self.pos < len(self.source) else None

    def _peek(self, offset: int = 1):
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def _skip_inline_whitespace(self):
        """Skip spaces and tabs (but NOT newlines — those are statement separators)."""
        while self._ch in (' ', '\t', '\r'):
            self._advance()

    def _skip_comment(self):
        """Skip from # to end of line."""
        while self._ch and self._ch != '\n':
            self._advance()

    # ── scanning helpers ─────────────────────

    def _scan_number(self) -> Token:
        line  = self.line
        start = self.pos
        is_float = False

        while self._ch and self._ch.isdigit():
            self._advance()

        if self._ch == '.' and self._peek() and self._peek().isdigit():
            is_float = True
            self._advance()          # consume '.'
            while self._ch and self._ch.isdigit():
                self._advance()

        raw = self.source[start:self.pos]
        if is_float:
            return Token(TT.FLOAT, float(raw), line)
        return Token(TT.INTEGER, int(raw), line)

    def _scan_identifier_or_keyword(self) -> Token:
        line  = self.line
        start = self.pos
        while self._ch and (self._ch.isalnum() or self._ch == '_'):
            self._advance()
        word   = self.source[start:self.pos]
        upper  = word.upper()
        if upper in KEYWORDS:
            return Token(TT.KEYWORD, upper, line)
        return Token(TT.IDENTIFIER, word, line)

    # ── public API ───────────────────────────

    def tokenize(self) -> list:
        """
        Walk the source and produce the full token list.
        Returns a list ending with an EOF token.
        """
        tokens: list[Token] = []

        while self.pos < len(self.source):
            self._skip_inline_whitespace()

            ch = self._ch
            if ch is None:
                break

            line = self.line

            # ── comment ──────────────────────
            if ch == '#':
                self._skip_comment()
                continue

            # ── newline (statement boundary) ─
            if ch == '\n':
                # Collapse consecutive blank lines into one NEWLINE token
                if not tokens or tokens[-1].type != TT.NEWLINE:
                    tokens.append(Token(TT.NEWLINE, '\n', line))
                self._advance()
                continue

            # ── number literal ────────────────
            if ch.isdigit():
                tokens.append(self._scan_number())
                continue

            # ── identifier / keyword ──────────
            if ch.isalpha() or ch == '_':
                tokens.append(self._scan_identifier_or_keyword())
                continue

            # ── two-character operators ───────
            two = ch + (self._peek() or '')
            if two in ('==', '!=', '<=', '>='):
                tokens.append(Token(TT.COMPARISON, two, line))
                self._advance(); self._advance()
                continue

            # ── single-character tokens ───────
            single_map = {
                '+': TT.PLUS,
                '-': TT.MINUS,
                '*': TT.MULTIPLY,
                '/': TT.DIVIDE,
                '%': TT.MODULO,
                '(': TT.LPAREN,
                ')': TT.RPAREN,
            }
            if ch in single_map:
                tokens.append(Token(single_map[ch], ch, line))
                self._advance()
                continue

            if ch == '=':
                tokens.append(Token(TT.EQUALS, '=', line))
                self._advance()
                continue

            if ch in ('<', '>'):
                tokens.append(Token(TT.COMPARISON, ch, line))
                self._advance()
                continue

            # ── unknown character ─────────────
            raise LexerError(
                f"Line {self.line}: unexpected character {ch!r}"
            )

        tokens.append(Token(TT.EOF, None, self.line))
        return tokens
