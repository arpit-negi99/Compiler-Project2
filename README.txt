═══════════════════════════════════════════════════════════════
  Algo2Code — Section 1: Algorithm Parser & Simulator
  README
═══════════════════════════════════════════════════════════════

OVERVIEW
────────
Section 1 is the first module of the Algo2Code three-section
pipeline. It reads a pseudo-code algorithm, parses it into an
Abstract Syntax Tree (AST), simulates execution, and produces
a JSON output that Section 2 (Code Generator) will consume.

This module intentionally generates NO C++ or Python code —
that responsibility belongs to Section 2.


PROJECT STRUCTURE
─────────────────
algo2code/
├── main.py                     ← Entry point (run this)
├── requirements.txt
├── README.txt                  ← This file
│
├── src/                        ← Core library (one file per concern)
│   ├── __init__.py
│   ├── ast_nodes.py            ← AST node class definitions
│   ├── lexer.py                ← Tokeniser
│   ├── parser.py               ← Recursive-descent parser
│   ├── interpreter.py          ← Tree-walking interpreter / simulator
│   ├── ast_printer.py          ← Human-readable AST pretty-printer
│   └── serializer.py           ← JSON export for Section 2
│
└── examples/                   ← Ready-to-run algorithm files
    ├── sum.algo                 # Sum of 1..n  (1 input, 1 output)
    ├── factorial.algo           # n!           (1 input, 1 output)
    ├── multi_input_output.algo  # n+m, n*m     (2 inputs, 2 outputs)
    ├── even_odd.algo            # IF/ELSE demo  (1 input, 2 outputs)
    ├── times_table.algo         # n×1..m        (2 inputs, m outputs)
    └── countdown.algo           # WHILE demo    (1 input, n outputs)


REQUIREMENTS
────────────
  Python ≥ 3.10
  No third-party packages required.


QUICK START
───────────
  # Run with a built-in example:
  python main.py examples/sum.algo

  # Interactive editor (type algorithm, finish with END_ALGO):
  python main.py

  # Skip the final Y/N prompt (useful in scripts):
  python main.py examples/factorial.algo --no-prompt


SUPPORTED PSEUDO-CODE LANGUAGE
───────────────────────────────

  READ variable
      Reads a value for 'variable' from user input.

  SET variable = expression
      Assigns the result of an expression to a variable.

  PRINT expression
      Outputs the value of an expression.

  FOR variable = start TO end
      ...body...
  END
      Counted loop from start to end (inclusive).
      Both start and end may be expressions.
      The loop variable increments/decrements automatically.

  IF condition
      ...body...
  ELSE
      ...body...
  END
      Conditional branching. ELSE is optional.

  WHILE condition
      ...body...
  END
      Pre-condition loop. Capped at 100,000 iterations for safety.

Expressions support:
  +  -  *  /   (standard arithmetic, left-associative)
  ( )          (grouping)
  -x           (unary negation)

Conditions support:
  ==  !=  <  >  <=  >=


EXAMPLE ALGORITHM  (examples/sum.algo)
──────────────────────────────────────
  READ n
  SET sum = 0
  FOR i = 1 TO n
      SET sum = sum + i
  END
  PRINT sum

  With input n = 5:
    Output #1 → 15


EXAMPLE WITH MULTIPLE INPUTS & OUTPUTS  (examples/times_table.algo)
────────────────────────────────────────────────────────────────────
  READ n
  READ m
  FOR i = 1 TO m
      SET product = n * i
      PRINT product
  END

  With n = 3, m = 4:
    Output #1 → 3
    Output #2 → 6
    Output #3 → 9
    Output #4 → 12


OUTPUT FILE  (section1_output.json)
────────────────────────────────────
After a successful run, Section 1 writes section1_output.json
with the following structure:

  {
    "algo2code_section": 1,
    "source_code": "...",
    "ast": {
      "type": "Program",
      "statements": [ ... ]
    },
    "simulation": {
      "status": "success",
      "inputs":    { "n": 5 },
      "outputs":   [ 15 ],
      "variables": { "n": 5, "sum": 15, "i": 5 },
      "read_order": [ "n" ]
    }
  }

Section 2 reads this file via:
  from src.serializer import load_result
  data = load_result("section1_output.json")


SECTION PIPELINE
────────────────
  Section 1  →  section1_output.json  →  Section 2  →  Section 3
  (this file)    (shared contract)        (codegen)      (compiler)


EMBEDDING SECTION 1 AS A LIBRARY
──────────────────────────────────
  from src import Lexer, Parser, Interpreter, serialize_result

  source = open("my_algo.algo").read()
  tokens  = Lexer(source).tokenize()
  program = Parser(tokens).parse()

  interp = Interpreter()
  interp.set_inputs({"n": 10})
  interp.execute(program)

  payload = serialize_result(program, interp.execution_result, source)
  # payload is a dict ready for JSON serialisation


ERROR MESSAGES
──────────────
  [LEXER ERROR]    — unrecognised character in source
  [PARSE ERROR]    — syntax violation (missing END, bad expression, etc.)
  [RUNTIME ERROR]  — undefined variable, division by zero, infinite loop


ARCHITECTURE NOTES (for Section 2 integration)
───────────────────────────────────────────────
  • The Interpreter is stateless between runs; call reset() to reuse.
  • set_inputs() accepts the inputs dict before execute().
  • execution_result is a plain dict — no AST objects — safe to serialise.
  • The JSON AST in section1_output.json mirrors the internal node
    structure exactly, so Section 2 can reconstruct or traverse it.
  • All node types are tagged with a "type" string field.


═══════════════════════════════════════════════════════════════
