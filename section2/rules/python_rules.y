%{
/*
 * ============================================================
 *   Algo2Code Compiler  -  Section 2
 *   File   : python_rules.y
 *   Target : Python 3
 *   Purpose: Yacc/Bison-style parser rule file for AST-to-Python translation
 *
 *   Grammar rules define the structure and code generation patterns
 *   for various AST node types when targeting Python.
 *
 *   Rule format:
 *       node_type: param_list { $$ = code_template; }
 *
 *   Placeholders are substituted using $1, $2, etc. referencing parameters
 * ============================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Language configuration */
#define LANGUAGE "python"
#define INDENT_SIZE 4

%}

/* Union for different semantic values */
%union {
    char* str;
    int num;
    struct node_list* list;
}

/* Token declarations */
%token READ PRINT ASSIGN FOR WHILE IF IFELSE
%token <str> IDENTIFIER NUMBER STRING
%token <str> BINARY_OP UNARY_OP

/* Type declarations */
%type <str> expression statement statements condition
%type <list> param_list

/* Grammar rules */
%%

program:
    statements 
    {
        /* Generate complete Python program */
        generate_python_program($1);
    }
    ;

statements:
    statement
    | statements statement
    ;

statement:
    READ '(' IDENTIFIER ')'
    {
        /* Read(var) -> {var} = int(input()) */
        char* code = malloc(256);
        sprintf(code, "%s = int(input())", $3);
        $$ = code;
    }
    | PRINT '(' expression ')'
    {
        /* Print(expr) -> print({expr}) */
        char* code = malloc(256);
        sprintf(code, "print(%s)", $3);
        $$ = code;
    }
    | ASSIGN '(' IDENTIFIER ',' expression ')'
    {
        /* Assign(var, expr) -> {var} = {expr} */
        char* code = malloc(256);
        sprintf(code, "%s = %s", $3, $5);
        $$ = code;
    }
    | FOR '(' IDENTIFIER ',' expression ',' expression ')' statement
    {
        /* For(var, start, end) BLOCK -> for {var} in range({start}, {end}+1): */
        char* code = malloc(512);
        sprintf(code, "for %s in range(%s, %s+1):\n    %s", 
                $3, $5, $7, $9);
        $$ = code;
    }
    | WHILE '(' condition ')' statement
    {
        /* While(condition) BLOCK -> while {condition}: */
        char* code = malloc(512);
        sprintf(code, "while %s:\n    %s", $3, $5);
        $$ = code;
    }
    | IF '(' condition ')' statement
    {
        /* If(condition) BLOCK -> if {condition}: */
        char* code = malloc(512);
        sprintf(code, "if %s:\n    %s", $3, $5);
        $$ = code;
    }
    | IFELSE '(' condition ')' statement ELSE statement
    {
        /* IfElse(condition) BLOCK_ELSE -> if {condition}: else: */
        char* code = malloc(512);
        sprintf(code, "if %s:\n    %s\nelse:\n    %s", $3, $5, $7);
        $$ = code;
    }
    ;

expression:
    IDENTIFIER
    | NUMBER
    | STRING
    | expression BINARY_OP expression
    {
        char* code = malloc(256);
        sprintf(code, "%s %s %s", $1, $2, $3);
        $$ = code;
    }
    | UNARY_OP expression
    {
        char* code = malloc(256);
        sprintf(code, "%s%s", $1, $2);
        $$ = code;
    }
    | '(' expression ')'
    {
        $$ = $2;
    }
    ;

condition:
    expression
    | expression '<' expression
    | expression '>' expression
    | expression '<' '=' expression
    | expression '>' '=' expression
    | expression '=' '=' expression
    | expression '!' '=' expression
    | expression '&' '&' expression
    {
        /* Convert && to and */
        char* code = malloc(256);
        sprintf(code, "%s and %s", $1, $3);
        $$ = code;
    }
    | expression '|' '|' expression
    {
        /* Convert || to or */
        char* code = malloc(256);
        sprintf(code, "%s or %s", $1, $3);
        $$ = code;
    }
    ;

%%

/* Helper functions */
void generate_python_program(struct node_list* statements) {
    /* Output statements with proper indentation */
    if (statements) {
        output_statements_python(statements);
    }
}

void output_statements_python(struct node_list* stmts) {
    while (stmts) {
        printf("    %s\n", stmts->code);
        stmts = stmts->next;
    }
}

void yyerror(const char* s) {
    fprintf(stderr, "Parse error: %s\n", s);
}

int main() {
    printf("Python Parser Rules Loaded\n");
    return 0;
}
