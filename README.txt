# Algo2Code - Algorithm to Code Compiler

## Overview
Algo2Code is a compiler that converts pseudo-code algorithms into working C++ and Python code.

## Features
- Parse pseudo-code algorithms
- Simulate algorithm execution
- Generate C++ and Python code
- Web interface for easy use

## Quick Start

### Web Interface
1. Run the web server:
   ```bash
   python final_web_server.py
   ```
2. Open your browser to `http://localhost:8000`
3. Enter your algorithm and compile

### Command Line
```bash
python unified_main.py --file examples/sum.algo --inputs '{"n": 5}'
```

## Algorithm Syntax

### Input/Output
```
READ variable_name
PRINT expression
```

### Assignment
```
SET variable = expression
```

### Loops
```
FOR variable = start TO end
    // loop body
END
```

### Conditionals
```
IF condition
    // if body
ELSE
    // else body
END
```

## Examples

### Sum of Numbers
```
READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum
```

### Factorial
```
READ n
SET fact = 1
FOR i = 1 TO n
    SET fact = fact * i
END
PRINT fact
```

## Project Structure
- `src/` - Core compiler components
- `section2/` - Code generation rules
- `examples/` - Sample algorithms
- `final_web_server.py` - Web interface
- `unified_main.py` - Command line interface

## Requirements
- Python 3.7+
- No external dependencies required
