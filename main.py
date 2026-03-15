#!/usr/bin/env python3
"""
Algo2Code Section 1: Algorithm Parser & Simulator
Main entry point for parsing and simulating pseudo-code algorithms.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParseError
from src.interpreter import Interpreter, InterpreterError
from src.serializer import serialize_result

def read_algorithm_file(filepath):
    """Read algorithm from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file '{filepath}': {e}")
        sys.exit(1)

def parse_inputs(inputs_str):
    """Parse inputs from string to dictionary"""
    if not inputs_str:
        return {}
    
    try:
        return json.loads(inputs_str)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format for inputs: {inputs_str}")
        sys.exit(1)

def run_algorithm(algorithm_text, inputs=None):
    """Run the complete algorithm pipeline"""
    try:
        # Lexer
        print("🔍 Lexing...")
        lexer = Lexer(algorithm_text)
        tokens = lexer.tokenize()
        print(f"✅ Lexer: {len(tokens)} tokens generated")
        
        # Parser
        print("🔧 Parsing...")
        parser = Parser(tokens)
        ast = parser.parse()
        print("✅ Parser: AST built successfully")
        
        # Interpreter
        print("⚡ Simulating...")
        interpreter = Interpreter()
        if inputs:
            interpreter.set_inputs(inputs)
        interpreter.execute(ast)
        result = interpreter.execution_result
        print("✅ Interpreter: Simulation completed")
        
        return ast, result
        
    except LexerError as e:
        print(f"❌ Lexer Error: {e}")
        sys.exit(1)
    except ParseError as e:
        print(f"❌ Parser Error: {e}")
        sys.exit(1)
    except InterpreterError as e:
        print(f"❌ Interpreter Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Algo2Code Section 1: Algorithm Parser & Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --file algorithm.algo
  python main.py --file algorithm.algo --inputs '{"n": 5}'
  python main.py --text "READ n\\nPRINT n" --inputs '{"n": 10}'
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', help='Algorithm file to process')
    input_group.add_argument('--text', '-t', help='Algorithm text to process')
    
    # Input values
    parser.add_argument('--inputs', '-i', help='Input values as JSON string')
    
    # Output options
    parser.add_argument('--output', '-o', default='section1_output.json', 
                       help='Output file for results (default: section1_output.json)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("🎯 Algo2Code Section 1: Algorithm Parser & Simulator")
    print("=" * 50)
    
    # Read algorithm
    if args.file:
        algorithm_text = read_algorithm_file(args.file)
        print(f"📁 Algorithm file: {args.file}")
    else:
        algorithm_text = args.text
        print("📝 Algorithm text provided")
    
    # Parse inputs
    inputs = parse_inputs(args.inputs) if args.inputs else {}
    if inputs:
        print(f"🎯 Input values: {inputs}")
    
    print()
    
    # Run algorithm
    ast, result = run_algorithm(algorithm_text, inputs)
    
    # Serialize and save results
    print("💾 Saving results...")
    payload = serialize_result(ast, result, algorithm_text)
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        print(f"✅ Results saved to: {args.output}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        sys.exit(1)
    
    print()
    print("📊 Simulation Results:")
    print(f"   Inputs: {result.get('inputs', {})}")
    print(f"   Outputs: {result.get('outputs', [])}")
    print(f"   Variables: {result.get('variables', {})}")
    
    print()
    print("🎉 Algorithm processing completed successfully!")

if __name__ == "__main__":
    main()
