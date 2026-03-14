%{
/*
 * ============================================================
 *   Algo2Code Compiler  -  Section 2
 *   File   : cpp_rules.y
 *   Target : C++17
 *   Purpose: Yacc/Bison-style parser rule file for AST-to-C++ translation
 *
 *   Grammar rules define the structure and code generation patterns
 *   for various AST node types when targeting C++.
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

/* Global configuration */
static char* header_code[] = {
    "#include <iostream>",
    "using namespace std;",
    "",
    "int main(){"
};

static char* footer_code[] = {
    "return 0;",
    "}"
};

/* Language configuration */
#define LANGUAGE "cpp"
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
        /* Generate complete C++ program */
        generate_cpp_program($1);
    }
    ;

statements:
    statement
    | statements statement
    ;

statement:
    READ '(' IDENTIFIER ')'
    {
        /* Read(var) -> int {var}; cin >> {var}; */
        char* code = malloc(256);
        sprintf(code, "int %s;\ncin >> %s;", $3, $3);
        $$ = code;
    }
    | PRINT '(' expression ')'
    {
        /* Print(expr) -> cout << {expr} << endl; */
        char* code = malloc(256);
        sprintf(code, "cout << %s << endl;", $3);
        $$ = code;
    }
    | ASSIGN '(' IDENTIFIER ',' expression ')'
    {
        /* Assign(var, expr) -> {var} = {expr}; */
        char* code = malloc(256);
        sprintf(code, "%s = %s;", $3, $5);
        $$ = code;
    }
    | FOR '(' IDENTIFIER ',' expression ',' expression ')' statement
    {
        /* For(var, start, end) BLOCK -> for(int {var} = {start}; {var} <= {end}; {var}++){ } */
        char* code = malloc(512);
        sprintf(code, "for(int %s = %s; %s <= %s; %s++){\n%s\n}", 
                $3, $5, $3, $7, $3, $9);
        $$ = code;
    }
    | WHILE '(' condition ')' statement
    {
        /* While(condition) BLOCK -> while({condition}){ } */
        char* code = malloc(512);
        sprintf(code, "while(%s){\n%s\n}", $3, $5);
        $$ = code;
    }
    | IF '(' condition ')' statement
    {
        /* If(condition) BLOCK -> if({condition}){ } */
        char* code = malloc(512);
        sprintf(code, "if(%s){\n%s\n}", $3, $5);
        $$ = code;
    }
    | IFELSE '(' condition ')' statement ELSE statement
    {
        /* IfElse(condition) BLOCK_ELSE -> if({condition}){ } else { } */
        char* code = malloc(512);
        sprintf(code, "if(%s){\n%s\n}\nelse{\n%s\n}", $3, $5, $7);
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
    | expression '|' '|' expression
    ;

%%

/* Helper functions */
void generate_cpp_program(struct node_list* statements) {
    int i;
    
    /* Output header */
    for (i = 0; i < sizeof(header_code)/sizeof(header_code[0]); i++) {
        printf("%s\n", header_code[i]);
    }
    
    /* Output statements */
    if (statements) {
        output_statements(statements);
    }
    
    /* Output footer */
    for (i = 0; i < sizeof(footer_code)/sizeof(footer_code[0]); i++) {
        printf("%s\n", footer_code[i]);
    }
}

void yyerror(const char* s) {
    fprintf(stderr, "Parse error: %s\n", s);
}

int main() {
    printf("C++ Parser Rules Loaded\n");
    return 0;
}
