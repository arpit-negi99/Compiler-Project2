# 🚀 Algo2Code Compiler

A powerful compiler that converts pseudo-code algorithms into working **C++** and **Python** code using traditional compiler construction tools (lex/yacc rules).

## ✨ Features

- 🔄 **Complete Pipeline**: Parse → Simulate → Generate Code in one step
- 🐍 **Python Generation**: Convert algorithms to Python 3 code
- 🚀 **C++ Generation**: Convert algorithms to C++17 code  
- 🌐 **Web Interface**: User-friendly web-based algorithm editor
- 📝 **Lex/Yacc Rules**: Traditional compiler construction approach
- 🎯 **Algorithm Simulation**: Test algorithms with custom inputs
- 📊 **Real-time Results**: See simulation outputs and variable states

## 🏗️ Project Structure

```
Algo2Code/
├── 📁 src/                    # Section 1: Parser & Simulator
│   ├── lexer.py              # Tokenizer
│   ├── parser.py             # AST parser  
│   ├── interpreter.py        # Algorithm simulator
│   └── serializer.py         # JSON export
├── 📁 section2/               # Section 2: Code Generator
│   ├── rule_engine.py        # Lex/Yacc rule processor
│   ├── expression_converter.py # Expression to string converter
│   ├── ast_traverser.py      # AST traversal engine
│   └── 📁 rules/             # Lex/Yacc rule files
│       ├── cpp_rules.l       # C++ lex rules
│       ├── cpp_rules.y       # C++ yacc rules
│       ├── python_rules.l    # Python lex rules
│       └── python_rules.y    # Python yacc rules
├── 📁 web/                    # Web interface (Node.js)
│   ├── package.json          # Node.js dependencies
│   ├── app/                  # Next.js app structure
│   └── components/           # React components
├── 📁 examples/               # Example algorithms
├── 🐍 unified_main.py         # Unified command-line interface
├── 🌐 web_server.py          # Web server backend
└── 📖 README.md              # This file
```

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

1. **Start the web server:**
   ```bash
   python web_server.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8000`

3. **Write your algorithm:**
   Use the built-in editor with syntax highlighting and examples

#### Option 3: Command Line
```bash
# Interactive mode:
python unified_main.py

# File mode:
python unified_main.py --file examples/sum.algo

# With custom inputs:
python unified_main.py --file examples/sum.algo --inputs '{"n": 5}'
```

## 📖 Algorithm Syntax

### 📥 Input/Output
```pseudo
READ variable_name
PRINT expression
```

### 🔧 Assignment
```pseudo
SET variable = expression
```

### 🔄 Loops
```pseudo
FOR variable = start TO end
    // loop body
END
```

### 🎯 Conditionals
```pseudo
IF condition
    // if body
ELSE
    // else body (optional)
END
```

### 🔁 While Loop
```pseudo
WHILE condition
    // loop body
END
```

### 📚 Supported Operations
- **Arithmetic:** `+`, `-`, `*`, `/`
- **Comparisons:** `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logic:** `AND`, `OR`, `NOT`
- **Variables:** Any valid identifier
- **Numbers:** Integers and floats

## 💡 Example Algorithms

### Sum of Numbers
```pseudo
READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum
```

### Factorial
```pseudo
READ n
SET fact = 1
FOR i = 1 TO n
    SET fact = fact * i
END
PRINT fact
```

### Even/Odd Check
```pseudo
READ n
IF n % 2 == 0
    PRINT "Even"
ELSE
    PRINT "Odd"
END
```

## 🔧 Installation & Setup

### Prerequisites
- **Python 3.10+** (for the compiler)
- **Node.js 18+** (for the web interface - optional)

### Setup Steps

1. **Clone/Download the project:**
   ```bash
   git clone <repository-url>
   cd Algo2Code
   ```

2. **Python Setup:**
   ```bash
   # No additional packages needed - uses only Python standard library
   python --version  # Should be 3.10 or higher
   ```

3. **Web Interface Setup (Optional):**
   ```bash
   cd web
   npm install
   cd ..
   ```

## 🌐 Web Interface Features

### 🎨 Modern UI
- Clean, responsive design
- Syntax-highlighted algorithm editor
- Real-time code generation
- Tabbed output display

### 📝 Interactive Editor
- Auto-resizing text area
- Syntax guide sidebar
- Example algorithms library
- One-click example loading

### ⚡ Live Compilation
- Instant C++ and Python generation
- Simulation results display
- Error handling and feedback
- Input value customization

### 📊 Results Display
- **Python Code:** Generated Python 3 code
- **C++ Code:** Generated C++17 code  
- **Simulation Results:** Inputs, outputs, and variable states

## 🛠️ Advanced Usage

### Custom Rule Development

The compiler uses lex (.l) and yacc (.y) files for code generation rules:

1. **Add new language rules:**
   - Create `newlang_rules.l` and `newlang_rules.y`
   - Define patterns and code templates
   - Update the rule engine to recognize new language

2. **Modify existing rules:**
   - Edit files in `section2/rules/`
   - Test with the unified compiler

### API Usage

The web server provides a REST API:

```bash
# Health check
curl http://localhost:8000/api/health

# Compile algorithm
curl -X POST http://localhost:8000/api/compile \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "READ n\nPRINT n", "inputs": {"n": 5}}'
```

## 🧪 Testing

### Test Examples
```bash
# Test with built-in examples
python unified_main.py --file examples/sum.algo
python unified_main.py --file examples/factorial.algo

# Test web interface
python web_server.py
# Open http://localhost:8000
```

### Expected Output
For the sum algorithm with input `{"n": 5}`:

**Generated Python:**
```python
n = int(input())
sum = 0

for i in range(1, n+1):
    sum = sum + i

print(sum)
```

**Generated C++:**
```cpp
#include <iostream>
using namespace std;

int main(){
    int n;
    cin >> n;
    
    int sum = 0;
    
    for(int i = 1; i <= n; i++){
        sum = sum + i;
    }
    
    cout << sum << endl;
    return 0;
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"Python version too old"**
   - Ensure Python 3.10+ is installed
   - Check with `python --version`

2. **"Module not found" errors**
   - Run from the project root directory
   - Ensure all files are present

3. **"Compilation failed"**
   - Check algorithm syntax
   - Verify input JSON format
   - Use the syntax guide for reference

4. **Web interface not loading**
   - Ensure `web_server.py` can run
   - Check if port 8000 is available
   - Try `python web_server.py` manually

### Getting Help

- 📖 Check the **Syntax Guide** in the web interface
- 💡 Try the **Example Algorithms** 
- 🐛 Report issues with detailed error messages
- 📧 Include algorithm code and expected output

## 🎯 Use Cases

### 📚 Education
- Teach algorithm concepts
- Demonstrate language differences
- Learn compiler construction

### 💻 Development
- Rapid prototyping
- Code generation templates
- Language translation

### 🔬 Research
- Algorithm analysis
- Language design
- Compiler techniques

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with traditional compiler construction tools
- Uses lex/yacc pattern matching principles
- Inspired by modern compiler design
- Created for educational and practical purposes

---

**🚀 Happy Compiling!**

Convert your pseudo-code algorithms to working C++ and Python code in seconds! 🎉
