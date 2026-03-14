%{
/*
 * ============================================================
 *   Algo2Code Compiler  -  Section 2
 *   File   : cpp_rules.l
 *   Target : C++17
 *   Purpose: Lex-style rule file for AST-to-C++ translation
 *
 *   Rule format:
 *       NodeType(param1, param2, ...)
 *           [BLOCK | BLOCK_ELSE]       <- wraps an indented body
 *           -> open line               <- template(s) before body
 *           [ELSE]                     <- else-branch separator
 *           -> else-open line
 *           [CLOSE]                    <- marker for closing brace
 *           -> }                       <- closing line template
 *       ;
 *
 *   Placeholders {param} are substituted at traversal time.
 *   HEADER lines prepend the file; FOOTER lines append the file.
 * ============================================================
 */

LANGUAGE    = cpp
INDENT_SIZE = 4
HEADER      = #include <iostream>
HEADER      = using namespace std;
HEADER      =
HEADER      = int main(){
FOOTER      = return 0;
FOOTER      = }
%}

%%

/* ---- I/O Statements ---------------------------------------- */

Read(var)
    -> int {var};
    -> cin >> {var};
;

Print(expr)
    -> cout << {expr} << endl;
;

/* ---- Assignment --------------------------------------------- */

Assign(var, expr)
    -> {var} = {expr};
;

/* ---- Loops -------------------------------------------------- */

For(var, start, end)
    BLOCK
    -> for(int {var} = {start}; {var} <= {end}; {var}++){
    CLOSE
    -> }
;

While(condition)
    BLOCK
    -> while({condition}){
    CLOSE
    -> }
;

/* ---- Conditionals ------------------------------------------ */

If(condition)
    BLOCK
    -> if({condition}){
    CLOSE
    -> }
;

IfElse(condition)
    BLOCK_ELSE
    -> if({condition}){
    ELSE
    -> } else {
    CLOSE
    -> }
;

%%

/* End of C++ Rules */
