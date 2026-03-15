#!/usr/bin/env python3
"""
Algo2Code Unified Compiler
Complete pipeline from pseudo-code to C++/Python code
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add project paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'section2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nodes'))

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParseError
from src.interpreter import Interpreter, InterpreterError
from src.serializer import serialize_result, save_result
from nodes.main_codegen import generate_python, generate_cpp

def run_section1(algorithm_text, inputs_override=None):
    """Run Section 1: Parse and simulate algorithm"""
    print("=" * 60)
    print("🔧 Section 1: Algorithm Parser & Simulator")
    print("=" * 60)
    
    try:
        # Lexer
        lexer = Lexer(algorithm_text)  # Pass the algorithm text to lexer
        tokens = lexer.tokenize()
        print(f"✅ Lexer: {len(tokens)} tokens generated")
        
        # Parser
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"✅ Parser: AST built successfully")
        
        # Interpreter
        interpreter = Interpreter()
        # Handle different input formats
        if isinstance(inputs_override, dict):
            interpreter.set_inputs(inputs_override)
        elif isinstance(inputs_override, (int, float, str)):
            # Single value - assign to 'n'
            interpreter.set_inputs({'n': inputs_override})
        else:
            interpreter.set_inputs(inputs_override or {})
        interpreter.execute(ast)
        result = interpreter.execution_result
        print(f"✅ Interpreter: Simulation completed")
        
        # Save result
        output_path = "section1_output.json"
        from src.serializer import serialize_result
        payload = serialize_result(ast, result, algorithm_text)
        with open(output_path, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)
        print(f"✅ Output saved to {output_path}")
        
        return result
        
    except (LexerError, ParseError, InterpreterError) as e:
        print(f"❌ Error in Section 1: {e}")
        return None

def run_section2():
    """Run Section 2: Generate C++ and Python code"""
    print("\n" + "=" * 60)
    print("⚡ Section 2: Code Generation")
    print("=" * 60)
    
    try:
        # Load AST
        with open("section1_output.json", 'r') as f:
            json_data = json.load(f)
        ast_root = json_data.get('ast', {})
        
        # Get paths
        section2_dir = Path("section2")
        rules_dir = section2_dir / "rules"
        
        # Generate Python
        print("🐍 Generating Python...")
        python_code = generate_python(ast_root, str(rules_dir))
        with open("generated_python.py", 'w') as f:
            f.write(python_code)
        print("✅ Python code generated: generated_python.py")
        
        # Generate C++
        print("🚀 Generating C++...")
        cpp_code = generate_cpp(ast_root, str(rules_dir))
        with open("generated_cpp.cpp", 'w') as f:
            f.write(cpp_code)
        print("✅ C++ code generated: generated_cpp.cpp")
        
        return python_code, cpp_code
        
    except Exception as e:
        print(f"❌ Error in Section 2: {e}")
        return None, None

def run_complete_pipeline(algorithm_text, inputs_override=None):
    """Run the complete Algo2Code pipeline"""
    print("🎯 Algo2Code Unified Compiler")
    print("🔄 Starting complete pipeline...\n")
    
    # Section 1
    result = run_section1(algorithm_text, inputs_override)
    if not result:
        return False, None, None
    
    # Show simulation results
    print("\n📊 Simulation Results:")
    print(f"   Inputs: {result.get('inputs', {})}")
    print(f"   Outputs: {result.get('outputs', [])}")
    print(f"   Variables: {result.get('variables', {})}")
    
    # Section 2
    python_code, cpp_code = run_section2()
    if python_code is None or cpp_code is None:
        return False, None, None
    
    print("\n🎉 Pipeline completed successfully!")
    return True, python_code, cpp_code

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Algo2Code Unified Compiler')
    parser.add_argument('--file', help='Algorithm file to process')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    parser.add_argument('--inputs', help='JSON string of inputs (e.g., \'{"n": 5}\')')
    
    args = parser.parse_args()
    
    if args.web:
        # Start web interface
        print("🌐 Starting web interface...")
        subprocess.run([sys.executable, 'web_server.py'])
        return
    
    # Get algorithm text
    if args.file:
        try:
            with open(args.file, 'r') as f:
                algorithm_text = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return
    else:
        # Interactive mode
        print("📝 Enter your algorithm (type 'END_ALGO' on a new line when finished):")
        lines = []
        while True:
            line = input("> ")
            if line.strip() == "END_ALGO":
                break
            lines.append(line)
        algorithm_text = "\n".join(lines)
    
    # Parse inputs
    inputs_override = {}
    if args.inputs:
        try:
            inputs_override = json.loads(args.inputs)
        except json.JSONDecodeError:
            print("❌ Invalid JSON format for inputs")
            return
    
    # Run pipeline
    success, python_code, cpp_code = run_complete_pipeline(algorithm_text, inputs_override)
    
    if success:
        print("\n" + "=" * 60)
        print("📋 Generated Code Preview:")
        print("=" * 60)
        print("\n🐍 Python Code:")
        print("-" * 30)
        print(python_code)
        print("\n🚀 C++ Code:")
        print("-" * 30)
        print(cpp_code)
        print(f"\n💾 Files saved: generated_python.py, generated_cpp.cpp")

if __name__ == "__main__":
    main()
