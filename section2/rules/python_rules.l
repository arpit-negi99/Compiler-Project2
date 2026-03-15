%{
/*
 * ============================================================
 *   Algo2Code Compiler  -  Section 2
 *   File   : python_rules.l
 *   Target : Python 3
 *   Purpose: Lex-style rule file for AST-to-Python translation
 *
 *   Rule format:
 *       NodeType(param1, param2, ...)
 *           [BLOCK | BLOCK_ELSE]       <- optional block marker
 *           -> template line           <- substitution template
 *           [ELSE]                     <- else-branch separator
 *           -> template line
 *           [CLOSE]                    <- closing marker (unused in Python)
 *       ;
 *
 *   Placeholders {param} are substituted at traversal time.
 * ============================================================
 */

LANGUAGE    = python
INDENT_SIZE = 4
%}

%%

/* ---- I/O Statements ---------------------------------------- */

Read(var)
    -> {var} = int(input())
;

Print(expr)
    -> print({expr})
;

/* ---- Assignment --------------------------------------------- */

Assign(var, expr)
    -> {var} = {expr}
;

/* ---- Loops -------------------------------------------------- */

For(var, start, end)
    BLOCK
    -> for {var} in range({start}, {end}+1):
;

ForReverse(var, start, end)
    BLOCK
    -> for {var} in range({start}, {end}-1, -1):
;

While(condition)
    BLOCK
    -> while {condition}:
;

/* ---- Conditionals ------------------------------------------ */

If(condition)
    BLOCK
    -> if {condition}:
;

IfElse(condition)
    BLOCK_ELSE
    -> if {condition}:
    ELSE
    -> else:
;

/* ---- Expressions -------------------------------------------- */

BinaryOp(left, op, right)
    -> ({left} {op} {right})
;

UnaryOp(op, operand)
    -> {op}{operand}
;

Number(value)
    -> {value}
;

Variable(name)
    -> {name}
;

/* ---- Conditions --------------------------------------------- */

Condition(left, op, right)
    -> ({left} {op} {right})
;

%%

/* End of Python Rules */
