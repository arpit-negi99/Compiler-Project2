# 2. Feature Scope

## Feature Overview & Current Status

### Core Features (v1.0 - Production) ✅

Algo2Code implements a complete **three-stage compiler pipeline**:

| Stage | Feature | Status | Details |
|---|---|---|---|
| **Stage 1: Lexical Analysis** | Tokenization | ✅ Complete | Breaks input into meaningful tokens |
| **Stage 2: Syntax/Semantic** | Parsing → AST | ✅ Complete | Builds Abstract Syntax Tree |
| **Stage 3: Simulation** | Algorithm Execution | ✅ Complete | Executes with inputs, traces state |
| **Stage 4: Code Generation** | C++ Output | ✅ Complete | Generates C++17 code |
| **Stage 4: Code Generation** | Python Output | ✅ Complete | Generates Python 3 code |
| **Interfaces** | Web UI | ✅ Complete | Interactive browser-based interface |
| **Interfaces** | CLI | ✅ Complete | Command-line + JSON API |

---

## Supported Language Features

### Data Types

| Type | Status | Example | C++ Mapping | Python Mapping |
|---|---|---|---|---|
| **Integer** | ✅ Supported | `SET n = 5` | `int` | Dynamic (int) |
| **Float** | ✅ Supported | `SET pi = 3.14` | `double` | Dynamic (float) |
| **Variable** | ✅ Supported | `SET x = y + 1` | Type inferred | Dynamic |
| **Array** | ❌ Phase 1 | N/A | Planned Q2 2026 | Planned Q2 2026 |
| **String** | ❌ Phase 3 | N/A | Planned Q3 2026 | Planned Q3 2026 |
| **Custom Type** | ❌ Out of Scope | N/A | Future (2027+) | Future (2027+) |

### Operators (11 Total)

#### **Arithmetic Operators** (5)
| Operator | Meaning | Example | C++ | Python |
|---|---|---|---|---|
| `+` | Addition | `SET result = a + b` | `a + b` | `a + b` |
| `-` | Subtraction | `SET result = a - b` | `a - b` | `a - b` |
| `*` | Multiplication | `SET result = a * b` | `a * b` | `a * b` |
| `/` | Division | `SET result = a / b` | `a / b` | `a / b` |
| `%` | Modulo | `SET result = a % b` | `a % b` | `a % b` |

#### **Relational Operators** (6)
| Operator | Meaning | Example | C++ | Python |
|---|---|---|---|---|
| `==` | Equal | `IF x == 5` | `x == 5` | `x == 5` |
| `!=` | Not Equal | `IF x != 0` | `x != 0` | `x != 0` |
| `<` | Less Than | `IF x < 10` | `x < 10` | `x < 10` |
| `>` | Greater Than | `IF x > 0` | `x > 0` | `x > 0` |
| `<=` | Less or Equal | `IF x <= n` | `x <= n` | `x <= n` |
| `>=` | Greater or Equal | `IF x >= 1` | `x >= 1` | `x >= 1` |

#### **Logical Operators** (3)
| Operator | Meaning | Example | C++ | Python |
|---|---|---|---|---|
| `AND` | Logical AND | `IF a > 0 AND b > 0` | `a > 0 && b > 0` | `a > 0 and b > 0` |
| `OR` | Logical OR | `IF x < 0 OR x > 10` | `x < 0 \|\| x > 10` | `x < 0 or x > 10` |
| `NOT` | Logical NOT | `IF NOT done` | `!done` | `not done` |

### Control Flow Statements (7)

| Statement | Syntax | Example | Purpose |
|---|---|---|---|
| **READ** | `READ variable` | `READ n` | Input from user |
| **PRINT** | `PRINT expression` | `PRINT sum` | Output result |
| **SET** | `SET var = expression` | `SET x = y + 1` | Variable assignment |
| **IF** | `IF condition ... END` | `IF x > 0 PRINT "pos" END` | Conditional execution |
| **ELSE** | `IF ... ELSE ... END` | `IF x > 0 ... ELSE ... END` | Alternative branch |
| **FOR** | `FOR var = start TO end ... END` | `FOR i = 1 TO n ... END` | Loop (fixed range) |
| **WHILE** | `WHILE condition ... END` | `WHILE x > 0 ... END` | Loop (conditional) |

---

## Feature Examples: Pseudo-Code → Generated Code

### Example 1: Simple Assignment

```
PSEUDO-CODE:
SET x = 5
SET y = x + 3
PRINT y

C++ OUTPUT:
int x, y;
x = 5;
y = x + 3;
cout << y << endl;

PYTHON OUTPUT:
x = 5
y = x + 3
print(y)
```

### Example 2: For Loop (Summation)

```
PSEUDO-CODE:
READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum

C++ OUTPUT:
int n, sum, i;
cin >> n;
sum = 0;
for(int i = 1; i <= n; i++) {
    sum = sum + i;
}
cout << sum << endl;
return 0;

PYTHON OUTPUT:
n = int(input())
sum = 0
for i in range(1, n + 1):
    sum = sum + i
print(sum)
```

### Example 3: Conditional Logic

```
PSEUDO-CODE:
READ x
IF x > 0
    PRINT "positive"
ELSE
    PRINT "non-positive"
END

C++ OUTPUT:
int x;
cin >> x;
if(x > 0) {
    cout << "positive" << endl;
} else {
    cout << "non-positive" << endl;
}
return 0;

PYTHON OUTPUT:
x = int(input())
if x > 0:
    print("positive")
else:
    print("non-positive")
```

### Example 4: While Loop

```
PSEUDO-CODE:
READ n
WHILE n > 0
    PRINT n
    SET n = n - 1
END

C++ OUTPUT:
int n;
cin >> n;
while(n > 0) {
    cout << n << endl;
    n = n - 1;
}
return 0;

PYTHON OUTPUT:
n = int(input())
while n > 0:
    print(n)
    n = n - 1
```

### Example 5: Nested Control Flow

```
PSEUDO-CODE:
READ rows
FOR i = 1 TO rows
    FOR j = 1 TO i
        PRINT "*"
    END
    PRINT "newline"
END

C++ OUTPUT:
int rows, i, j;
cin >> rows;
for(int i = 1; i <= rows; i++) {
    for(int j = 1; j <= i; j++) {
        cout << "*" << endl;
    }
    cout << "newline" << endl;
}
return 0;

PYTHON OUTPUT:
rows = int(input())
for i in range(1, rows + 1):
    for j in range(1, i + 1):
        print("*")
    print("newline")
```

---

## Technical Architecture

### High-Level Data Flow

```
INPUT: Algorithm File (sum.algo)
  ├─ Content: READ n; SET sum = 0; FOR i = 1 TO n...
  └─ Size: <200 lines, pure ASCII
  
          ↓ [SECTION 1: PARSING & ANALYSIS]
          
LEXER (src/lexer.py)
  ├─ Input: Raw source code string
  ├─ Process: Character-by-character tokenization
  ├─ Output: Token stream [READ, IDENTIFIER(n), SET, ...]
  └─ Error Handling: Invalid chars → tokenization error
  
          ↓ [SECTION 1: PARSING & ANALYSIS]
          
PARSER (src/parser.py)
  ├─ Input: Token stream
  ├─ Process: Recursive descent parsing, grammar matching
  ├─ Output: Abstract Syntax Tree (AST)
  │  └─ Node types: StmtNode, ExprNode, LoopNode, etc.
  └─ Error Handling: Syntax errors → helpful messages
  
          ↓ [SECTION 1: PARSING & ANALYSIS]
          
AST PRINTER (src/ast_printer.py)
  ├─ Purpose: Debug visualization
  ├─ Output: Tree representation of structure
  └─ Usage: Understanding parse results
  
          ↓ [IF SIMULATION REQUESTED]
          
INTERPRETER (src/interpreter.py)
  ├─ Input: AST + User input values
  ├─ Process: AST traversal, instruction execution
  ├─ Maintains: Variable symbol table, execution trace
  ├─ Output: 
  │  ├─ Output values (from PRINT statements)
  │  ├─ Variable state trace (values at each step)
  │  └─ Errors (undefined variable, division by zero)
  └─ Memory: Symbol table, call stack (future)
  
          ↓ [SECTION 2: CODE GENERATION]
          
RULE ENGINE (section2/rule_engine.py)
  ├─ Input: AST
  ├─ Process: Language-specific rule matching & traversal
  │  ├─ Rule file: cpp_rules.l, cpp_rules.y
  │  ├─ Rule file: python_rules.l, python_rules.y
  │  └─ Pattern matching: AST nodes → code patterns
  ├─ Output: Target language code snippets
  └─ Modes: C++ generation OR Python generation
  
          ↓ [CODE FORMATTING]
          
FORMATTER (section2/ + nodes/)
  ├─ Input: Generated code snippets
  ├─ Process: 
  │  ├─ Add headers/imports
  │  ├─ Proper indentation
  │  ├─ Main function wrapper
  │  └─ Syntax cleanup
  ├─ Output: 
  │  ├─ C++ file (complete, runnable)
  │  └─ Python file (complete, runnable)
  └─ Verification: Compile/run check (optional)
  
          ↓ [SERIALIZATION]
          
SERIALIZER (src/serializer.py)
  ├─ Purpose: Convert results to JSON
  ├─ Contents:
  │  ├─ AST structure
  │  ├─ Simulation results
  │  ├─ Generated code (both languages)
  │  └─ Any errors
  └─ Usage: API responses, debugging
  
OUTPUT: JSON Response
  ├─ Code Generation: {"cpp_code": "...", "python_code": "..."}
  ├─ Simulation: {"output": [15], "variables": {"n": 5, "sum": 15}}
  ├─ AST Debug: {"ast": {...}}
  └─ Errors: {"errors": ["Unexpected token on line 3"]}
```

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                          │
│  ┌──────────────────────┐    ┌──────────────────────────┐   │
│  │   WEB INTERFACE      │    │  CLI / BATCH PROCESSING  │   │
│  │  (HTML + JavaScript) │    │  python unified_main.py  │   │
│  └────┬─────────────────┘    └──────┬───────────────────┘   │
└───────┼──────────────────────────────┼(JSON I/O)─────────────┘
        │ HTTP POST                    │ stdin/stdout
        ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│         UNIFIED ENTRY POINT (nodes/main_codegen.py)         │
│  ├─ Accepts: algorithm text + input values                 │
│  ├─ Routes to: Parser/Generator pipeline                   │
│  └─ Returns: JSON results (both languages)                 │
└───────┬──────────────────────────────────────────────────────┘
        │ Orchestrates
        ▼
    ┌─────────────────────────────────────────────┐
    │   SECTION 1: Parsing & Simulation (src/)    │
    ├─────────────────────────────────────────────┤
    │                                             │
    │  lexer.py            → Tokenization        │
    │     ↓                                        │
    │  parser.py           → AST Construction    │
    │     ↓                                        │
    │  interpreter.py      → Simulation Logic    │
    │     ↓                                        │
    │  serializer.py       → JSON Output         │
    │                                             │
    └─────────────────────────────────────────────┘
            ↓ (AST + Simulation Results)
    ┌─────────────────────────────────────────────┐
    │   SECTION 2: Code Generation (section2/)    │
    ├─────────────────────────────────────────────┤
    │                                             │
    │  rule_engine.py      → Pattern Matching    │
    │  ast_traverser.py    → AST Traversal       │
    │  expression_converter.py → Operator Mapping│
    │                                             │
    │  rules/cpp_rules.l   → C++ Lex Rules       │
    │  rules/cpp_rules.y   → C++ Yacc Rules      │
    │                                             │
    │  rules/python_rules.l → Python Lex Rules   │
    │  rules/python_rules.y → Python Yacc Rules  │
    │                                             │
    └─────────────────────────────────────────────┘
            ↓ (Code snippets)
    ┌─────────────────────────────────────────────┐
    │   Formatting & Final Output                │
    │   ├─ Add headers/imports                   │
    │   ├─ Indentation                           │
    │   ├─ Main function wrapper                 │
    │   └─ Language-specific syntax              │
    └─────────────────────────────────────────────┘
            ↓
    ┌─────────────────────────────────────────────┐
    │   FINAL OUTPUT                              │
    ├─────────────────────────────────────────────┤
    │  C++17 Code        Python 3 Code            │
    │  ┌────────────┐    ┌────────────┐           │
    │  │#include... │    │import...   │           │
    │  │int main... │    │def main... │           │
    │  │return 0;   │    │...         │           │
    │  └────────────┘    └────────────┘           │
    └─────────────────────────────────────────────┘
```

### Component Dependencies

```
CORE MODULES:
├─ src/lexer.py              (No dependencies except Python stdlib)
├─ src/parser.py             → Requires: lexer, ast_nodes
├─ src/ast_nodes.py          → Requires: None
├─ src/interpreter.py        → Requires: ast_nodes
├─ src/serializer.py         → Requires: ast_nodes
└─ src/ast_printer.py        → Requires: ast_nodes

CODE GENERATION:
├─ section2/rule_engine.py   → Requires: ast_nodes, traverser, expression_converter
├─ section2/ast_traverser.py → Requires: ast_nodes
├─ section2/expression_converter.py → Requires: ast_nodes
└─ section2/rules/*.{l,y}    → No code dependencies (rule files)

ORCHESTRATION:
└─ nodes/main_codegen.py     → Requires: All of above

WEB/CLI:
├─ simple_web_server.py      → Requires: nodes/main_codegen
└─ unified_main.py           → Requires: nodes/main_codegen
```

---

## Development Roadmap

### Phase 0: STABLE PRODUCTION (NOW - v1.0) ✅

**Status**: Complete, deployed to production

**What's Done**:
- ✅ Core pipeline (lexing, parsing, interpretation, generation)
- ✅ C++17 + Python 3 output
- ✅ Web interface operational
- ✅ CLI available
- ✅ Example algorithms included
- ✅ Deployment configured (Render.com)

**No breaking changes planned for v1.0. Maintenance-only mode.**

---

### Phase 1: Arrays & Data Structures (Q2 2026 - 3 Weeks)

**Goal**: Enable algorithms using arrays

**Breakdown**:

#### Task 1.1: Lexer Enhancement (5 days)
- Tokenize `[` `]` for array indexing
- Add ARRAY syntax recognition
- Example: `SET arr[0] = 5`
- **Effort**: 5 developer-days

#### Task 1.2: Parser & AST Nodes (5 days)
- Create ArrayNode, ArrayAccessNode, ArrayAssignmentNode
- Update grammar for array operations
- Support multi-dimensional arrays
- **Effort**: 5 developer-days
- **Dependencies**: Task 1.1

#### Task 1.3: Interpreter (4 days)
- Array variable tracking in symbol table
- Bounds checking + runtime errors
- Loop-based array iteration
- Array state in execution trace
- **Effort**: 4 developer-days
- **Dependencies**: Task 1.2

#### Task 1.4: Code Generation (6 days)
- C++ rules: `int arr[SIZE]`, `arr[i] = value`
- Python rules: `arr = [0] * size`, `arr[i]`
- Dynamic vs. static allocation
- **Effort**: 6 developer-days
- **Dependencies**: Task 1.3

#### Task 1.5: Testing & Examples (2 days)
- 10 example algorithms (bubble sort, linear search, etc.)
- Edge case testing
- Documentation updates
- **Effort**: 2 developer-days
- **Dependencies**: Task 1.4

**Phase 1 Total**: 22 developer-days (can parallelize)
**Team**: 1–2 developers
**Release**: v1.1 (April–June 2026)

---

### Phase 2: Functions & Recursion (Q3 2026 - 4 Weeks)

**Goal**: Enable user-defined functions and recursive algorithms

**Tasks**:
- Lexer: FUNCTION, RETURN keywords (4 days)
- Parser: FunctionDefNode, FunctionCallNode (6 days)
- Interpreter: Call stack, scope management (7 days)
- Code generation: Function signatures, return types (7 days)
- Testing: Recursion (factorial, fibonacci) (3 days)

**Phase 2 Total**: 27 developer-days
**Team**: 2 developers
**Dependencies**: Phase 1 recommended (but independent)
**Release**: v1.2 (August 2026)

---

### Phase 3: String Support (Q3 2026 - 2 Weeks)

**Goal**: Enable string operations for text processing

**Tasks**:
- Lexer: String literals, quote handling (3 days)
- Parser: StringNode, string operations (3 days)
- Interpreter: String operations + concatenation (2 days)
- Code generation: C++ std::string, Python str (4 days)
- Testing: String algorithms (2 days)

**Phase 3 Total**: 14 developer-days
**Team**: 1 developer
**Can run parallel**: With Phase 2
**Release**: v1.2 (August 2026)

---

### Phase 4: New Language Targets (Q4 2026 - 3+ Weeks per Language)

**Goal**: Support Java, Go, Rust, JavaScript

**Per Language Breakdown** (e.g., Java):
- Study language syntax (2 days)
- Write rule files (java_rules.l, java_rules.y) (7 days)
- Implement generator (7 days)
- Testing + validation (4 days)
- Documentation (3 days)

**Total per language**: 3–4 weeks
**Languages in 2026**: Java, Go
**Release**: v1.3 (November 2026)

---

### Phase 5: Optimization Passes (2027+)

**Features**:
- Dead code elimination (2 weeks)
- Constant folding (2 weeks)
- Interactive debugger (3 weeks)
- Optimization levels (-O0, -O1, -O2) (1 week)

**Release**: v2.0 (June 2027)

---

## Testing Plan

### Unit Testing

#### **Lexer Tests** (40+ tests)
- Valid token stream generation
- Invalid character rejection
- Edge cases (empty input, deep nesting)
- **Target Coverage**: 95%

#### **Parser Tests** (60+ tests)
- Correct AST construction
- Syntax error detection
- Nested statement handling
- **Target Coverage**: 90%

#### **Interpreter Tests** (50+ tests)
- Correct execution logic
- Variable state tracking
- Error handling (undefined var, div by zero)
- **Target Coverage**: 85%

#### **Code Generator Tests** (80+ tests)
- C++ code compiles with g++17
- Python code runs with Python 3.10+
- Output matches expected format
- **Target Coverage**: 80%

### Integration Testing

#### **End-to-End Workflows** (20+ scenarios)
- Upload → Simulate → Generate complete flow
- CLI JSON I/O validation
- Web API request/response handling

#### **Generated Code Validation** (30+ algorithms)
- Compile generated C++ successfully
- Run generated Python successfully
- Output matches simulation results

### Performance Testing

| Test | Target | Method |
|---|---|---|
| Parse 100-line algorithm | <500ms | Benchmark |
| Simulate algorithm | <1s | Benchmark |
| Generate code | <500ms | Benchmark |
| Web request (end-to-end) | <2s | Integration |
| Concurrent users | 50+ | Load test |

### User Acceptance Testing

- 10 CS students evaluate UX
- Feedback collection: clarity, usefulness, learning value
- Survey: "Did you understand compiler concepts?" (target: 80%+ yes)

---

## API Specifications

### REST Endpoints

#### **POST /api/compile**
Generate code + simulate algorithm

```json
REQUEST:
{
  "code": "READ n\nSET sum = 0\nFOR i = 1 TO n\n  SET sum = sum + i\nEND\nPRINT sum",
  "inputs": {"n": 5},
  "simulate": true
}

RESPONSE:
{
  "status": "success",
  "ast": { ... },
  "simulation": {
    "output": [15],
    "variables": {"n": 5, "sum": 15, "i": 6},
    "trace": [...]
  },
  "cpp_code": "#include <iostream>...",
  "python_code": "n = int(input())...",
  "errors": []
}
```

#### **POST /api/generate**
Generate code only (skip simulation)

```json
REQUEST:
{
  "code": "...",
  "language": "cpp"
}

RESPONSE:
{
  "language": "cpp",
  "generated_code": "#include <iostream>..."
}
```

---

## Summary: Feature Completeness Status

**Implemented (v1.0)** ✅:
- Lexical analysis, parsing, AST construction
- Algorithm simulation with I/O tracing
- C++17 & Python 3 generation
- Web + CLI interfaces
- Arithmetic, logical, control flow

**Planned (2026)** 📅:
- Arrays, strings (Phase 1–3)
- Functions, recursion (Phase 2)
- New languages (Phase 4)

**Future (2027+)** 🔮:
- Optimization passes
- Interactive debugger
- Visualization tools
- Advanced data structures
- OOP support (optional)
