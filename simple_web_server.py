#!/usr/bin/env python3
"""
Algo2Code Simple Web Server
Focus on better UX with simple input formats and two-step workflow
"""

import sys
import os
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from urllib.parse import parse_qs, urlparse

# Add project paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'section2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nodes'))

from unified_main import run_complete_pipeline

class Algo2CodeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_html()
        elif parsed_path.path == '/api/health':
            self.send_json_response({"status": "ok", "message": "Algo2Code API is running"})
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/execute':
            self.handle_execute()
        elif parsed_path.path == '/api/generate':
            self.handle_generate()
        elif parsed_path.path == '/api/detect-variables':
            self.handle_detect_variables()
        else:
            self.send_error(404, "Not Found")
    
    def handle_execute(self):
        """Handle algorithm execution (simulation only)"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            algorithm = request_data.get('algorithm', '')
            # Fix escaped newlines - handle both literal and JSON escapes
            algorithm = algorithm.replace('\\\\n', '\n').replace('\\\\r', '\r').replace('\\\\t', '\t')
            algorithm = algorithm.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
            inputs_text = str(request_data.get('inputs', '')).strip()
            
            if not algorithm.strip():
                self.send_json_response({
                    "error": "Algorithm cannot be empty"
                }, status=400)
                return
            
            # Parse inputs - support multiple formats
            inputs = {}
            raw_inputs = request_data.get('inputs', '')
            
            # Handle if inputs is already a dict (from JSON)
            if isinstance(raw_inputs, dict):
                inputs = raw_inputs
            elif isinstance(raw_inputs, (int, float)):
                # Single numeric value - detect variable name from algorithm
                var_name = self._detect_first_input_variable(algorithm) or 'n'
                inputs = {var_name: raw_inputs}
            elif isinstance(raw_inputs, str) and raw_inputs.strip():
                inputs_text = raw_inputs.strip()
                try:
                    # Try JSON first
                    inputs = json.loads(inputs_text)
                except:
                    try:
                        # Simple format: "n=5,m=6" or "5,6"
                        if '=' in inputs_text:
                            # n=5,m=6 format
                            pairs = inputs_text.split(',')
                            for pair in pairs:
                                if '=' in pair:
                                    key, value = pair.split('=', 1)
                                    key = key.strip()
                                    value = value.strip()
                                    # Try to convert to int, fallback to float, then string
                                    try:
                                        inputs[key] = int(value)
                                    except ValueError:
                                        try:
                                            inputs[key] = float(value)
                                        except ValueError:
                                            inputs[key] = value
                        else:
                            # Auto-detect variables from algorithm
                            detected_vars = self._detect_input_variables(algorithm)
                            values = [x.strip() for x in inputs_text.split(',')]
                            for i, val in enumerate(values):
                                if i < len(detected_vars):
                                    var_name = detected_vars[i]
                                    # Try to convert to int, fallback to float, then string
                                    try:
                                        inputs[var_name] = int(val)
                                    except ValueError:
                                        try:
                                            inputs[var_name] = float(val)
                                        except ValueError:
                                            inputs[var_name] = val
                    except Exception as e:
                        print(f"Input parsing error: {e}")
                        inputs = {}
            
            # Run only Section 1 (simulation)
            from src.lexer import Lexer
            from src.parser import Parser  
            from src.interpreter import Interpreter
            from src.serializer import serialize_result
            
            try:
                # Lexer
                lexer = Lexer(algorithm)
                tokens = lexer.tokenize()
                
                # Parser
                parser = Parser(tokens)
                ast = parser.parse()
                
                # Interpreter
                interpreter = Interpreter()
                # Ensure inputs is always a dict
                if not inputs:
                    inputs = {}
                elif isinstance(inputs, (int, float)):
                    # Single value - detect variable name from algorithm
                    var_name = self._detect_first_input_variable(algorithm) or 'n'
                    inputs = {var_name: inputs}
                elif isinstance(inputs, str):
                    # Already processed string to dict above
                    pass  # inputs is already a dict
                # Now inputs should be a dict
                interpreter.set_inputs(inputs)
                interpreter.execute(ast)
                result = interpreter.execution_result
                
                # Save result
                from src.serializer import serialize_result
                payload = serialize_result(ast, result, algorithm)
                with open("section1_output.json", 'w', encoding='utf-8') as fh:
                    json.dump(payload, fh, indent=2)
                
                # Detect input variables (using the helper method)
                detected_vars = self._detect_input_variables(algorithm)
                
                # Send response
                response_data = {
                    "success": True,
                    "simulation_results": {
                        "inputs": result.get('inputs', {}),
                        "outputs": result.get('outputs', []),
                        "variables": result.get('variables', {})
                    },
                    "detected_inputs": detected_vars
                }
                
                self.send_json_response(response_data)
                
            except Exception as e:
                self.send_json_response({
                    "error": f"Execution error: {str(e)}"
                }, status=500)
                
        except json.JSONDecodeError:
            self.send_json_response({
                "error": "Invalid JSON in request body"
            }, status=400)
        except Exception as e:
            self.send_json_response({
                "error": f"Server error: {str(e)}"
            }, status=500)
    
    def handle_generate(self):
        """Handle code generation request"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            target = request_data.get('target', 'both')  # 'python', 'cpp', or 'both'
            
            # Read simulation results
            try:
                with open("section1_output.json", 'r') as f:
                    json_data = json.load(f)
                algorithm = json_data.get('source_code', '')
            except Exception as e:
                self.send_json_response({
                    "error": "No simulation results found. Please execute algorithm first."
                }, status=400)
                return
            
            # Run Section 2 (code generation)
            from nodes.main_codegen import generate_python, generate_cpp
            
            try:
                # Load AST from JSON
                ast_dict = json_data.get('ast', {})
                if not ast_dict:
                    self.send_json_response({
                        "error": "No AST found in simulation results"
                    }, status=400)
                    return
                
                # Generate code based on target
                python_code = ""
                cpp_code = ""
                
                # Get rules directory path
                rules_dir = os.path.join(os.path.dirname(__file__), 'section2', 'rules')
                
                if target in ['python', 'both']:
                    python_code = generate_python(ast_dict, rules_dir)
                
                if target in ['cpp', 'both']:
                    cpp_code = generate_cpp(ast_dict, rules_dir)
                
                # Send response
                response_data = {
                    "success": True,
                    "python_code": python_code,
                    "cpp_code": cpp_code
                }
                
                self.send_json_response(response_data)
                
            except Exception as e:
                import traceback
                error_msg = f"Code generation error: {str(e)}"
                print(f"ERROR: {error_msg}")
                traceback.print_exc()
                self.send_json_response({
                    "error": error_msg
                }, status=500)
                
        except json.JSONDecodeError:
            self.send_json_response({
                "error": "Invalid JSON in request body"
            }, status=400)
        except Exception as e:
            self.send_json_response({
                "error": f"Server error: {str(e)}"
            }, status=500)
    
    def handle_detect_variables(self):
        """Handle variable detection request"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            algorithm = request_data.get('algorithm', '')
            # Fix escaped newlines
            algorithm = algorithm.replace('\\\\n', '\n').replace('\\\\r', '\r').replace('\\\\t', '\t')
            algorithm = algorithm.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
            
            # Detect variables
            detected_vars = self._detect_input_variables(algorithm)
            
            self.send_json_response({
                "variables": detected_vars
            })
            
        except json.JSONDecodeError:
            self.send_json_response({
                "error": "Invalid JSON in request body"
            }, status=400)
        except Exception as e:
            self.send_json_response({
                "error": f"Server error: {str(e)}"
            }, status=500)
    
    def _detect_input_variables(self, algorithm: str) -> list:
        """Detect all input variables from READ statements in the algorithm"""
        detected_vars = []
        lines = algorithm.split('\n')
        for line in lines:
            stripped = line.strip()
            # Check for READ statement (case-insensitive)
            if stripped.upper().startswith('READ '):
                # Extract variable names after READ
                vars_part = stripped[5:].strip()
                # Handle multiple variables: READ n, m, x
                for var in vars_part.split(','):
                    var = var.strip()
                    if var and var not in detected_vars:
                        detected_vars.append(var)
        return detected_vars
    
    def _detect_first_input_variable(self, algorithm: str) -> str:
        """Detect the first input variable from READ statement"""
        vars_list = self._detect_input_variables(algorithm)
        return vars_list[0] if vars_list else None
    
    def serve_html(self):
        """Serve the main HTML page"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Algo2Code - Algorithm to Code Compiler</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .editor-container { height: 400px; border: 1px solid #e5e7eb; border-radius: 0.5rem; overflow: hidden; }
        .code-output { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 0.5rem; font-family: 'Courier New', monospace; font-size: 0.875rem; line-height: 1.5; overflow-x: auto; }
        .btn-primary { background: #3b82f6; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; border: none; font-weight: 500; }
        .btn-primary:hover { background: #2563eb; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .btn-secondary { background: #6b7280; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; border: none; font-weight: 500; }
        .btn-secondary:hover { background: #4b5563; transform: translateY(-1px); }
        .results-box { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1rem; margin-top: 1rem; transition: all 0.3s; }
        
        /* Light mode specific fixes */
        .enhanced-card { background: #ffffff; border: 1px solid #e5e7eb; }
        .text-gray-800 { color: #1f2937; }
        .text-gray-200 { color: #e5e7eb; }
        .text-blue-800 { color: #1e40af; }
        .text-blue-300 { color: #93c5fd; }
        .text-green-800 { color: #166534; }
        .text-green-300 { color: #86efac; }
        .text-purple-800 { color: #6b21a8; }
        .text-purple-300 { color: #d8b4fe; }
        .text-orange-800 { color: #9a3412; }
        .text-orange-300 { color: #fed7aa; }
        
        /* Dark mode styles */
        .dark { background: #0f172a; color: #e2e8f0; }
        .dark .bg-gray-50 { background: #0f172a; }
        .dark .bg-white { background: #1e293b; }
        .dark .text-gray-900 { color: #e2e8f0; }
        .dark .text-gray-600 { color: #94a3b8; }
        .dark .text-gray-700 { color: #cbd5e1; }
        .dark .text-gray-800 { color: #e2e8f0; }
        .dark .text-gray-200 { color: #94a3b8; }
        .dark .border-gray-200 { border-color: #334155; }
        .dark .border-gray-300 { border-color: #475569; }
        .dark .results-box { background: #1e293b; border-color: #334155; }
        .dark .code-output { background: #0f172a; }
        .dark .bg-blue-50 { background: #1e3a8a; }
        .dark .bg-green-50 { background: #14532d; }
        .dark .bg-purple-50 { background: #581c87; }
        .dark .bg-orange-50 { background: #7c2d12; }
        .dark .bg-gray-50 { background: #1e293b; }
        .dark .enhanced-card { background: #1e293b; border-color: #334155; }
        .dark .text-blue-800 { color: #93c5fd; }
        .dark .text-blue-300 { color: #1e40af; }
        .dark .text-green-800 { color: #86efac; }
        .dark .text-green-300 { color: #166534; }
        .dark .text-purple-800 { color: #d8b4fe; }
        .dark .text-purple-300 { color: #6b21a8; }
        .dark .text-orange-800 { color: #fed7aa; }
        .dark .text-orange-300 { color: #9a3412; }
        
        /* Enhanced styling */
        .gradient-text { background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .glass-effect { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
        .dark .glass-effect { background: rgba(30, 41, 59, 0.8); border-color: rgba(255, 255, 255, 0.1); }
        
        /* Theme toggle button */
        .theme-toggle { position: fixed; top: 1rem; right: 1rem; z-index: 50; background: #3b82f6; color: white; border: none; border-radius: 50%; width: 3rem; height: 3rem; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
        .theme-toggle:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15); }
        .dark .theme-toggle { background: #8b5cf6; }
        
        /* Input and textarea enhancements */
        .form-input { transition: all 0.2s; }
        .form-input:focus { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15); }
        .dark .form-input { background: #1e293b; border-color: #475569; color: #e2e8f0; }
        
        /* Card enhancements */
        .enhanced-card { transition: all 0.3s; }
        .enhanced-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); }
        
        /* Notification system */
        .notification { position: fixed; top: 5rem; right: 1rem; z-index: 100; max-width: 400px; transform: translateX(500px); transition: transform 0.3s ease-out; }
        .notification.show { transform: translateX(0); }
        .notification.success { background: linear-gradient(135deg, #10b981, #059669); color: white; border-left: 4px solid #059669; }
        .notification.error { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; border-left: 4px solid #dc2626; }
        .notification-content { padding: 1rem 1.5rem; display: flex; align-items: center; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15); border-radius: 0.5rem; }
        .notification-icon { font-size: 1.5rem; margin-right: 1rem; }
        .notification-message { flex: 1; font-weight: 500; }
        .notification-close { background: rgba(255, 255, 255, 0.2); border: none; color: white; width: 2rem; height: 2rem; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
        .notification-close:hover { background: rgba(255, 255, 255, 0.3); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Theme Toggle Button -->
    <button id="theme-toggle" class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">
        <span id="theme-icon">🌙</span>
    </button>
    
    <!-- Notification Container -->
    <div id="notification" class="notification">
        <div class="notification-content">
            <span class="notification-icon" id="notification-icon">✅</span>
            <span class="notification-message" id="notification-message">Success!</span>
            <button class="notification-close" onclick="hideNotification()" title="Close notification">
                <span>×</span>
            </button>
        </div>
    </div>
    
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-5xl font-bold mb-3">
                <span class="gradient-text">🚀 Algo2Code Compiler</span>
            </h1>
            <p class="text-xl text-gray-600 mb-4">Transform pseudo-code algorithms into production-ready C++ and Python code</p>
            <div class="flex justify-center gap-4 text-sm text-gray-500">
                <span class="glass-effect px-3 py-1 rounded-full">✨ Smart Variable Detection</span>
                <span class="glass-effect px-3 py-1 rounded-full">⚡ Real-time Execution</span>
                <span class="glass-effect px-3 py-1 rounded-full">🎯 Code Generation</span>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📝 Algorithm Editor</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="editor-container">
                        <textarea id="algorithm" class="form-input w-full h-full p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-300 rounded-lg" 
                                  placeholder="Enter your algorithm here..." 
                                  style="min-height: 400px;">READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum</textarea>
                    </div>
                    
                    <div class="mt-6">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">🎯 Input Values</label>
                        <div class="relative">
                            <input id="inputs" class="form-input w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                   placeholder="e.g., 5 or n=5,m=10 or 5,10">
                            <div class="absolute right-3 top-3 text-gray-400">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                        </div>
                        <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">Supports: single values, named variables, or comma-separated values</p>
                    </div>

                    <div class="mt-6 flex gap-3">
                        <button onclick="executeAlgorithm()" class="btn-primary flex-1 py-3 text-lg font-semibold">
                            ⚡ Execute Algorithm
                        </button>
                        <button onclick="clearResults()" class="btn-secondary px-6 py-3 font-semibold">
                            🗑️ Clear
                        </button>
                    </div>
                </div>
                
                <div id="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 hidden"></div>
            </div>

            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📊 Results</h2>
                
                <!-- Simulation Results -->
                <div id="simulation-results" class="enhanced-card bg-white rounded-lg shadow-lg p-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">📊</span>
                        </div>
                        <h3 class="text-xl font-bold text-blue-800 dark:text-blue-300">Simulation Results</h3>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">📥</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Inputs</strong>
                            </div>
                            <pre id="sim-inputs" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">📤</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Outputs</strong>
                            </div>
                            <pre id="sim-outputs" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">🔧</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Variables</strong>
                            </div>
                            <pre id="sim-variables" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                    </div>
                    <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg">
                        <div class="flex items-center">
                            <span class="text-lg mr-2">🎯</span>
                            <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">Detected input variables:</span>
                            <span id="input-vars" class="ml-2 text-sm font-mono text-blue-800 dark:text-blue-200">-</span>
                        </div>
                    </div>
                </div>

                <!-- Code Generation -->
                <div id="code-generation" class="enhanced-card bg-white rounded-lg shadow-lg p-6 mt-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">🚀</span>
                        </div>
                        <h3 class="text-xl font-bold text-green-800 dark:text-green-300">Generate Code</h3>
                    </div>
                    <div class="mb-6">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Choose target language:</label>
                        <div class="grid grid-cols-3 gap-3">
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="python" class="mr-2" checked>
                                <span class="text-sm font-medium">🐍 Python</span>
                            </label>
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="cpp" class="mr-2">
                                <span class="text-sm font-medium">🚀 C++</span>
                            </label>
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="both" class="mr-2">
                                <span class="text-sm font-medium">🐍🚀 Both</span>
                            </label>
                        </div>
                    </div>
                    <button onclick="generateCode()" class="btn-primary w-full py-3 text-lg font-semibold">
                        🚀 Generate Code
                    </button>
                </div>

                <!-- Generated Code -->
                <div id="code-output" class="enhanced-card bg-white rounded-lg shadow-lg p-6 mt-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">💻</span>
                        </div>
                        <h3 class="text-xl font-bold text-purple-800 dark:text-purple-300">Generated Code</h3>
                    </div>
                    <div class="flex space-x-2 mb-4">
                        <button onclick="showTab('python')" id="python-tab" class="btn-primary">🐍 Python</button>
                        <button onclick="showTab('cpp')" id="cpp-tab" class="btn-secondary">🚀 C++</button>
                    </div>
                    
                    <div class="code-output min-h-[400px] rounded-lg">
                        <div id="python-content" class="tab-content">
                            <div class="flex items-center mb-3 pb-2 border-b border-gray-700">
                                <span class="text-lg font-semibold text-green-400">🐍 Generated Python Code</span>
                            </div>
                            <pre id="python-code" class="text-sm text-gray-100">// No Python code generated yet</pre>
                        </div>
                        <div id="cpp-content" class="tab-content hidden">
                            <div class="flex items-center mb-3 pb-2 border-b border-gray-700">
                                <span class="text-lg font-semibold text-blue-400">🚀 Generated C++ Code</span>
                            </div>
                            <pre id="cpp-code" class="text-sm text-gray-100">// No C++ code generated yet</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📖 Algorithm Syntax Guide</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="space-y-4">
                        <div class="p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">📥</span>
                                <h4 class="font-semibold text-blue-800 dark:text-blue-300">Input/Output</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-blue-200 dark:border-blue-700 text-gray-900 dark:text-gray-100">READ variable_name
PRINT expression</pre>
                        </div>
                        <div class="p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🔧</span>
                                <h4 class="font-semibold text-green-800 dark:text-green-300">Assignment</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-green-200 dark:border-green-700 text-gray-900 dark:text-gray-100">SET variable = expression</pre>
                        </div>
                        <div class="p-4 bg-purple-50 dark:bg-purple-900 rounded-lg border border-purple-200 dark:border-purple-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🔄</span>
                                <h4 class="font-semibold text-purple-800 dark:text-purple-300">Loops</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-purple-200 dark:border-purple-700 text-gray-900 dark:text-gray-100">FOR variable = start TO end
    // loop body
END</pre>
                        </div>
                        <div class="p-4 bg-orange-50 dark:bg-orange-900 rounded-lg border border-orange-200 dark:border-orange-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🎯</span>
                                <h4 class="font-semibold text-orange-800 dark:text-orange-300">Conditionals</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-orange-200 dark:border-orange-700 text-gray-900 dark:text-gray-100">IF condition
    // if body
ELSE
    // else body (optional)
END</pre>
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">💡 Quick Tips</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="space-y-4">
                        <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <div class="flex items-center mb-3">
                                <span class="text-xl mr-2">📝</span>
                                <h4 class="font-semibold text-gray-800 dark:text-gray-200">Input Formats</h4>
                            </div>
                            <ul class="text-sm text-gray-600 dark:text-gray-300 space-y-2">
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Single number:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">5</code> (assigns to first detected variable)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Multiple numbers:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">5,10</code> (assigns to detected variables in order)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Named variables:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">n=5,m=10</code> (explicit assignment)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>JSON format:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">{"n": 5, "m": 10}</code></span>
                                </li>
                            </ul>
                        </div>
                        <div class="p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
                            <div class="flex items-center mb-3">
                                <span class="text-xl mr-2">🎯</span>
                                <h4 class="font-semibold text-green-800 dark:text-green-300">Workflow</h4>
                            </div>
                            <ol class="text-sm text-gray-600 dark:text-gray-300 space-y-2">
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">1</span>
                                    <span>Enter your algorithm in the editor</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">2</span>
                                    <span>Provide input values (optional)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">3</span>
                                    <span>Click "Execute Algorithm"</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">4</span>
                                    <span>Review simulation results</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">5</span>
                                    <span>Choose code generation target</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">6</span>
                                    <span>Get generated Python and C++ code</span>
                                </li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="mt-16 py-8 border-t border-gray-200 dark:border-gray-700">
            <div class="container mx-auto px-4 text-center">
                <div class="flex justify-center items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                    <span class="flex items-center">
                        <span class="text-lg mr-2">🚀</span>
                        Algo2Code Compiler
                    </span>
                    <span class="hidden md:inline">|</span>
                    <span class="flex items-center">
                        <span class="text-lg mr-2">⚡</span>
                        Smart Variable Detection
                    </span>
                    <span class="hidden md:inline">|</span>
                    <span class="flex items-center">
                        <span class="text-lg mr-2">🎯</span>
                        Real-time Code Generation
                    </span>
                </div>
                <p class="mt-4 text-xs text-gray-400 dark:text-gray-500">
                    Transform pseudo-code algorithms into production-ready Python and C++ code
                </p>
            </div>
        </footer>
    </div>

    <script>
        let currentTab = 'python';
        let notificationTimeout;
        
        // Notification system
        function showNotification(message, type = 'success', duration = 4000) {
            const notification = document.getElementById('notification');
            const icon = document.getElementById('notification-icon');
            const messageEl = document.getElementById('notification-message');
            
            // Clear existing timeout
            if (notificationTimeout) {
                clearTimeout(notificationTimeout);
            }
            
            // Set content and style
            messageEl.textContent = message;
            icon.textContent = type === 'success' ? '✅' : '❌';
            
            // Remove existing classes and add new ones
            notification.className = `notification ${type}`;
            
            // Show notification with animation
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            // Auto-hide after duration
            notificationTimeout = setTimeout(() => {
                hideNotification();
            }, duration);
        }
        
        function hideNotification() {
            const notification = document.getElementById('notification');
            notification.classList.remove('show');
            
            // Clear timeout
            if (notificationTimeout) {
                clearTimeout(notificationTimeout);
            }
        }
        
        // Theme management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            
            if (theme === 'dark') {
                document.documentElement.classList.add('dark');
                document.body.classList.add('dark');
                document.getElementById('theme-icon').textContent = '☀️';
            } else {
                document.getElementById('theme-icon').textContent = '🌙';
            }
        }
        
        function toggleTheme() {
            const isDark = document.documentElement.classList.toggle('dark');
            document.body.classList.toggle('dark');
            
            const icon = document.getElementById('theme-icon');
            icon.textContent = isDark ? '☀️' : '🌙';
            
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', initTheme);
        
        function showTab(tab) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id$="-tab"]').forEach(el => {
                el.classList.remove('btn-primary');
                el.classList.add('btn-secondary');
            });
            
            // Show selected tab
            document.getElementById(tab + '-content').classList.remove('hidden');
            document.getElementById(tab + '-tab').classList.remove('btn-secondary');
            document.getElementById(tab + '-tab').classList.add('btn-primary');
            
            currentTab = tab;
        }
        
        function clearResults() {
            document.getElementById('simulation-results').classList.add('hidden');
            document.getElementById('code-generation').classList.add('hidden');
            document.getElementById('code-output').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
        }
        
        async function executeWithInputs(algorithm, inputs) {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ algorithm, inputs }),
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Execution failed');
            }
            
            // Show simulation results
            document.getElementById('simulation-results').classList.remove('hidden');
            document.getElementById('sim-inputs').textContent = JSON.stringify(result.simulation_results.inputs, null, 2);
            document.getElementById('sim-outputs').textContent = JSON.stringify(result.simulation_results.outputs, null, 2);
            document.getElementById('sim-variables').textContent = JSON.stringify(result.simulation_results.variables, null, 2);
            document.getElementById('input-vars').textContent = result.detected_inputs.join(', ');
            
            // Show code generation section
            document.getElementById('code-generation').classList.remove('hidden');
        }
        
        async function executeAlgorithm() {
            const algorithm = document.getElementById('algorithm').value;
            const inputsText = document.getElementById('inputs').value;
            const errorDiv = document.getElementById('error');
            
            // Hide error
            errorDiv.classList.add('hidden');
            
            try {
                // Parse inputs to proper format
                let inputs = {};
                if (inputsText.trim()) {
                    try {
                        // Try JSON first
                        inputs = JSON.parse(inputsText);
                    } catch {
                        // Try simple format
                        if (inputsText.includes('=')) {
                            // n=5,m=6 format
                            const pairs = inputsText.split(',');
                            pairs.forEach(pair => {
                                const [key, value] = pair.split('=');
                                if (key && value) {
                                    inputs[key.trim()] = parseInt(value.trim());
                                }
                            });
                        } else {
                            // Simple number format - detect variables from algorithm first
                            const values = inputsText.split(',').map(v => parseInt(v.trim()));
                            
                            // Call API to detect variables first
                            fetch('/api/detect-variables', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ algorithm }),
                            })
                            .then(resp => resp.json())
                            .then(varResult => {
                                const detectedVars = varResult.variables || [];
                                values.forEach((val, i) => {
                                    if (i < detectedVars.length) {
                                        inputs[detectedVars[i]] = val;
                                    }
                                });
                                
                                // Now execute with proper inputs
                                executeWithInputs(algorithm, inputs);
                            })
                            .catch(() => {
                                // Fallback to default variable names
                                const varNames = ['n', 'm', 'a', 'b', 'x', 'y'];
                                values.forEach((val, i) => {
                                    if (i < varNames.length) {
                                        inputs[varNames[i]] = val;
                                    }
                                });
                                executeWithInputs(algorithm, inputs);
                            });
                            
                            return; // Exit early, we'll call executeWithInputs asynchronously
                        }
                    }
                }
                
                // Execute with parsed inputs
                executeWithInputs(algorithm, inputs);
                
            } catch (error) {
                errorDiv.textContent = '❌ ' + error.message;
                errorDiv.classList.remove('hidden');
            }
        }
        
        async function generateCode() {
            const errorDiv = document.getElementById('error');
            
            // Hide error
            errorDiv.classList.add('hidden');
            
            // Get selected target
            const selectedTarget = document.querySelector('input[name="target"]:checked').value;
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ target: selectedTarget }),
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Code generation failed');
                }
                
                // Hide code generation section and show code output
                document.getElementById('code-generation').classList.add('hidden');
                document.getElementById('code-output').classList.remove('hidden');
                
                // Update code outputs
                document.getElementById('python-code').textContent = result.python_code || '// No Python code generated';
                document.getElementById('cpp-code').textContent = result.cpp_code || '// No C++ code generated';
                
                // Show appropriate tab
                if (selectedTarget === 'python' || selectedTarget === 'both') {
                    showTab('python');
                } else if (selectedTarget === 'cpp' || selectedTarget === 'both') {
                    showTab('cpp');
                }
                
                showNotification('Code generation successful!', 'success');
                
            } catch (error) {
                showNotification(error.message || 'Code generation failed', 'error');
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8000):
    """Run the web server"""
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(__file__))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, Algo2CodeHandler)
    print(f"🌐 Algo2Code Web Server running at http://localhost:{port}")
    print("📝 Use the web interface to compile algorithms")
    print("⚡ Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

def _detect_input_variables(algorithm: str) -> list:
    """Detect all input variables from READ statements in the algorithm"""
    detected_vars = []
    lines = algorithm.split('\n')
    for line in lines:
        stripped = line.strip()
        # Check for READ statement (case-insensitive)
        if stripped.upper().startswith('READ '):
            # Extract variable names after READ
            vars_part = stripped[5:].strip()
            # Handle multiple variables: READ n, m, x
            for var in vars_part.split(','):
                var = var.strip()
                if var and var not in detected_vars:
                    detected_vars.append(var)
    return detected_vars

def _detect_first_input_variable(algorithm: str) -> str:
    """Detect the first input variable from READ statement"""
    vars_list = _detect_input_variables(algorithm)
    return vars_list[0] if vars_list else None

# WSGI application for Render/Gunicorn
def _get_html_content():
    """Get the HTML content for the main page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Algo2Code - Algorithm to Code Compiler</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .editor-container { height: 400px; border: 1px solid #e5e7eb; border-radius: 0.5rem; overflow: hidden; }
        .code-output { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 0.5rem; font-family: 'Courier New', monospace; font-size: 0.875rem; line-height: 1.5; overflow-x: auto; }
        .btn-primary { background: #3b82f6; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; border: none; font-weight: 500; }
        .btn-primary:hover { background: #2563eb; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .btn-secondary { background: #6b7280; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; border: none; font-weight: 500; }
        .btn-secondary:hover { background: #4b5563; transform: translateY(-1px); }
        .results-box { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1rem; margin-top: 1rem; transition: all 0.3s; }
        
        /* Light mode specific fixes */
        .enhanced-card { background: #ffffff; border: 1px solid #e5e7eb; }
        .text-gray-800 { color: #1f2937; }
        .text-gray-200 { color: #e5e7eb; }
        .text-blue-800 { color: #1e40af; }
        .text-blue-300 { color: #93c5fd; }
        .text-green-800 { color: #166534; }
        .text-green-300 { color: #86efac; }
        .text-purple-800 { color: #6b21a8; }
        .text-purple-300 { color: #d8b4fe; }
        .text-orange-800 { color: #9a3412; }
        .text-orange-300 { color: #fed7aa; }
        
        /* Dark mode styles */
        .dark { background: #0f172a; color: #e2e8f0; }
        .dark .bg-gray-50 { background: #0f172a; }
        .dark .bg-white { background: #1e293b; }
        .dark .text-gray-900 { color: #e2e8f0; }
        .dark .text-gray-600 { color: #94a3b8; }
        .dark .text-gray-700 { color: #cbd5e1; }
        .dark .text-gray-800 { color: #e2e8f0; }
        .dark .text-gray-200 { color: #94a3b8; }
        .dark .border-gray-200 { border-color: #334155; }
        .dark .border-gray-300 { border-color: #475569; }
        .dark .results-box { background: #1e293b; border-color: #334155; }
        .dark .code-output { background: #0f172a; }
        .dark .bg-blue-50 { background: #1e3a8a; }
        .dark .bg-green-50 { background: #14532d; }
        .dark .bg-purple-50 { background: #581c87; }
        .dark .bg-orange-50 { background: #7c2d12; }
        .dark .bg-gray-50 { background: #1e293b; }
        .dark .enhanced-card { background: #1e293b; border-color: #334155; }
        .dark .text-blue-800 { color: #93c5fd; }
        .dark .text-blue-300 { color: #1e40af; }
        .dark .text-green-800 { color: #86efac; }
        .dark .text-green-300 { color: #166534; }
        .dark .text-purple-800 { color: #d8b4fe; }
        .dark .text-purple-300 { color: #6b21a8; }
        .dark .text-orange-800 { color: #fed7aa; }
        .dark .text-orange-300 { color: #9a3412; }
        
        /* Enhanced styling */
        .gradient-text { background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .glass-effect { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
        .dark .glass-effect { background: rgba(30, 41, 59, 0.8); border-color: rgba(255, 255, 255, 0.1); }
        
        /* Theme toggle button */
        .theme-toggle { position: fixed; top: 1rem; right: 1rem; z-index: 50; background: #3b82f6; color: white; border: none; border-radius: 50%; width: 3rem; height: 3rem; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
        .theme-toggle:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15); }
        .dark .theme-toggle { background: #8b5cf6; }
        
        /* Input and textarea enhancements */
        .form-input { transition: all 0.2s; }
        .form-input:focus { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15); }
        .dark .form-input { background: #1e293b; border-color: #475569; color: #e2e8f0; }
        
        /* Card enhancements */
        .enhanced-card { transition: all 0.3s; }
        .enhanced-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); }
        
        /* Notification system */
        .notification { position: fixed; top: 5rem; right: 1rem; z-index: 100; max-width: 400px; transform: translateX(500px); transition: transform 0.3s ease-out; }
        .notification.show { transform: translateX(0); }
        .notification.success { background: linear-gradient(135deg, #10b981, #059669); color: white; border-left: 4px solid #059669; }
        .notification.error { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; border-left: 4px solid #dc2626; }
        .notification-content { padding: 1rem 1.5rem; display: flex; align-items: center; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15); border-radius: 0.5rem; }
        .notification-icon { font-size: 1.5rem; margin-right: 1rem; }
        .notification-message { flex: 1; font-weight: 500; }
        .notification-close { background: rgba(255, 255, 255, 0.2); border: none; color: white; width: 2rem; height: 2rem; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
        .notification-close:hover { background: rgba(255, 255, 255, 0.3); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Theme Toggle Button -->
    <button id="theme-toggle" class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">
        <span id="theme-icon">🌙</span>
    </button>
    
    <!-- Notification Container -->
    <div id="notification" class="notification">
        <div class="notification-content">
            <span class="notification-icon" id="notification-icon">✅</span>
            <span class="notification-message" id="notification-message">Success!</span>
            <button class="notification-close" onclick="hideNotification()" title="Close notification">
                <span>×</span>
            </button>
        </div>
    </div>
    
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-5xl font-bold mb-3">
                <span class="gradient-text">🚀 Algo2Code Compiler</span>
            </h1>
            <p class="text-xl text-gray-600 mb-4">Transform pseudo-code algorithms into production-ready C++ and Python code</p>
            <div class="flex justify-center gap-4 text-sm text-gray-500">
                <span class="glass-effect px-3 py-1 rounded-full">✨ Smart Variable Detection</span>
                <span class="glass-effect px-3 py-1 rounded-full">⚡ Real-time Execution</span>
                <span class="glass-effect px-3 py-1 rounded-full">🎯 Code Generation</span>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📝 Algorithm Editor</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="editor-container">
                        <textarea id="algorithm" class="form-input w-full h-full p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-300 rounded-lg" 
                                  placeholder="Enter your algorithm here..." 
                                  style="min-height: 400px;">READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum</textarea>
                    </div>
                    
                    <div class="mt-6">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">🎯 Input Values</label>
                        <div class="relative">
                            <input id="inputs" class="form-input w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                                   placeholder="e.g., 5 or n=5,m=10 or 5,10">
                            <div class="absolute right-3 top-3 text-gray-400">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                        </div>
                        <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">Supports: single values, named variables, or comma-separated values</p>
                    </div>

                    <div class="mt-6 flex gap-3">
                        <button onclick="executeAlgorithm()" class="btn-primary flex-1 py-3 text-lg font-semibold">
                            ⚡ Execute Algorithm
                        </button>
                        <button onclick="clearResults()" class="btn-secondary px-6 py-3 font-semibold">
                            🗑️ Clear
                        </button>
                    </div>
                </div>
                
                <div id="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 hidden"></div>
            </div>

            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📊 Results</h2>
                
                <!-- Simulation Results -->
                <div id="simulation-results" class="enhanced-card bg-white rounded-lg shadow-lg p-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">📊</span>
                        </div>
                        <h3 class="text-xl font-bold text-blue-800 dark:text-blue-300">Simulation Results</h3>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">📥</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Inputs</strong>
                            </div>
                            <pre id="sim-inputs" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">📤</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Outputs</strong>
                            </div>
                            <pre id="sim-outputs" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                            <div class="flex items-center mb-2">
                                <span class="text-lg mr-2">🔧</span>
                                <strong class="text-sm font-semibold text-gray-700 dark:text-gray-300">Variables</strong>
                            </div>
                            <pre id="sim-variables" class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">-</pre>
                        </div>
                    </div>
                    <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg">
                        <div class="flex items-center">
                            <span class="text-lg mr-2">🎯</span>
                            <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">Detected input variables:</span>
                            <span id="input-vars" class="ml-2 text-sm font-mono text-blue-800 dark:text-blue-200">-</span>
                        </div>
                    </div>
                </div>

                <!-- Code Generation -->
                <div id="code-generation" class="enhanced-card bg-white rounded-lg shadow-lg p-6 mt-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">🚀</span>
                        </div>
                        <h3 class="text-xl font-bold text-green-800 dark:text-green-300">Generate Code</h3>
                    </div>
                    <div class="mb-6">
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Choose target language:</label>
                        <div class="grid grid-cols-3 gap-3">
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="python" class="mr-2" checked>
                                <span class="text-sm font-medium">🐍 Python</span>
                            </label>
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="cpp" class="mr-2">
                                <span class="text-sm font-medium">🚀 C++</span>
                            </label>
                            <label class="flex items-center justify-center p-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
                                <input type="radio" name="target" value="both" class="mr-2">
                                <span class="text-sm font-medium">🐍🚀 Both</span>
                            </label>
                        </div>
                    </div>
                    <button onclick="generateCode()" class="btn-primary w-full py-3 text-lg font-semibold">
                        🚀 Generate Code
                    </button>
                </div>

                <!-- Generated Code -->
                <div id="code-output" class="enhanced-card bg-white rounded-lg shadow-lg p-6 mt-6 hidden">
                    <div class="flex items-center mb-4">
                        <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mr-3">
                            <span class="text-2xl">💻</span>
                        </div>
                        <h3 class="text-xl font-bold text-purple-800 dark:text-purple-300">Generated Code</h3>
                    </div>
                    <div class="flex space-x-2 mb-4">
                        <button onclick="showTab('python')" id="python-tab" class="btn-primary">🐍 Python</button>
                        <button onclick="showTab('cpp')" id="cpp-tab" class="btn-secondary">🚀 C++</button>
                    </div>
                    
                    <div class="code-output min-h-[400px] rounded-lg">
                        <div id="python-content" class="tab-content">
                            <div class="flex items-center mb-3 pb-2 border-b border-gray-700">
                                <span class="text-lg font-semibold text-green-400">🐍 Generated Python Code</span>
                            </div>
                            <pre id="python-code" class="text-sm text-gray-100">// No Python code generated yet</pre>
                        </div>
                        <div id="cpp-content" class="tab-content hidden">
                            <div class="flex items-center mb-3 pb-2 border-b border-gray-700">
                                <span class="text-lg font-semibold text-blue-400">🚀 Generated C++ Code</span>
                            </div>
                            <pre id="cpp-code" class="text-sm text-gray-100">// No C++ code generated yet</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">📖 Algorithm Syntax Guide</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="space-y-4">
                        <div class="p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">📥</span>
                                <h4 class="font-semibold text-blue-800 dark:text-blue-300">Input/Output</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-blue-200 dark:border-blue-700 text-gray-900 dark:text-gray-100">READ variable_name
PRINT expression</pre>
                        </div>
                        <div class="p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🔧</span>
                                <h4 class="font-semibold text-green-800 dark:text-green-300">Assignment</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-green-200 dark:border-green-700 text-gray-900 dark:text-gray-100">SET variable = expression</pre>
                        </div>
                        <div class="p-4 bg-purple-50 dark:bg-purple-900 rounded-lg border border-purple-200 dark:border-purple-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🔄</span>
                                <h4 class="font-semibold text-purple-800 dark:text-purple-300">Loops</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-purple-200 dark:border-purple-700 text-gray-900 dark:text-gray-100">FOR variable = start TO end
    // loop body
END</pre>
                        </div>
                        <div class="p-4 bg-orange-50 dark:bg-orange-900 rounded-lg border border-orange-200 dark:border-orange-700">
                            <div class="flex items-center mb-2">
                                <span class="text-xl mr-2">🎯</span>
                                <h4 class="font-semibold text-orange-800 dark:text-orange-300">Conditionals</h4>
                            </div>
                            <pre class="text-sm bg-white dark:bg-gray-900 p-3 rounded border border-orange-200 dark:border-orange-700 text-gray-900 dark:text-gray-100">IF condition
    // if body
ELSE
    // else body (optional)
END</pre>
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <h2 class="text-3xl font-bold mb-4 text-gray-800 dark:text-gray-200">💡 Quick Tips</h2>
                <div class="enhanced-card bg-white rounded-lg shadow-lg p-6">
                    <div class="space-y-4">
                        <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <div class="flex items-center mb-3">
                                <span class="text-xl mr-2">📝</span>
                                <h4 class="font-semibold text-gray-800 dark:text-gray-200">Input Formats</h4>
                            </div>
                            <ul class="text-sm text-gray-600 dark:text-gray-300 space-y-2">
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Single number:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">5</code> (assigns to first detected variable)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Multiple numbers:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">5,10</code> (assigns to detected variables in order)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>Named variables:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">n=5,m=10</code> (explicit assignment)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="text-blue-500 mr-2">•</span>
                                    <span><strong>JSON format:</strong> <code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">{"n": 5, "m": 10}</code></span>
                                </li>
                            </ul>
                        </div>
                        <div class="p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
                            <div class="flex items-center mb-3">
                                <span class="text-xl mr-2">🎯</span>
                                <h4 class="font-semibold text-green-800 dark:text-green-300">Workflow</h4>
                            </div>
                            <ol class="text-sm text-gray-600 dark:text-gray-300 space-y-2">
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">1</span>
                                    <span>Enter your algorithm in the editor</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">2</span>
                                    <span>Provide input values (optional)</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">3</span>
                                    <span>Click "Execute Algorithm"</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">4</span>
                                    <span>Review simulation results</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">5</span>
                                    <span>Choose code generation target</span>
                                </li>
                                <li class="flex items-start">
                                    <span class="bg-green-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2 mt-0.5">6</span>
                                    <span>Get generated Python and C++ code</span>
                                </li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="mt-16 py-8 border-t border-gray-200 dark:border-gray-700">
            <div class="container mx-auto px-4 text-center">
                <div class="flex justify-center items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                    <span class="flex items-center">
                        <span class="text-lg mr-2">🚀</span>
                        Algo2Code Compiler
                    </span>
                    <span class="hidden md:inline">|</span>
                    <span class="flex items-center">
                        <span class="text-lg mr-2">⚡</span>
                        Smart Variable Detection
                    </span>
                    <span class="hidden md:inline">|</span>
                    <span class="flex items-center">
                        <span class="text-lg mr-2">🎯</span>
                        Real-time Code Generation
                    </span>
                </div>
                <p class="mt-4 text-xs text-gray-400 dark:text-gray-500">
                    Transform pseudo-code algorithms into production-ready Python and C++ code
                </p>
            </div>
        </footer>
    </div>

    <script>
        let currentTab = 'python';
        let notificationTimeout;
        
        // Notification system
        function showNotification(message, type = 'success', duration = 4000) {
            const notification = document.getElementById('notification');
            const icon = document.getElementById('notification-icon');
            const messageEl = document.getElementById('notification-message');
            
            // Clear existing timeout
            if (notificationTimeout) {
                clearTimeout(notificationTimeout);
            }
            
            // Set content and style
            messageEl.textContent = message;
            icon.textContent = type === 'success' ? '✅' : '❌';
            
            // Remove existing classes and add new ones
            notification.className = `notification ${type}`;
            
            // Show notification with animation
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            // Auto-hide after duration
            notificationTimeout = setTimeout(() => {
                hideNotification();
            }, duration);
        }
        
        function hideNotification() {
            const notification = document.getElementById('notification');
            notification.classList.remove('show');
            
            // Clear timeout
            if (notificationTimeout) {
                clearTimeout(notificationTimeout);
            }
        }
        
        // Theme management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            
            if (theme === 'dark') {
                document.documentElement.classList.add('dark');
                document.body.classList.add('dark');
                document.getElementById('theme-icon').textContent = '☀️';
            } else {
                document.getElementById('theme-icon').textContent = '🌙';
            }
        }
        
        function toggleTheme() {
            const isDark = document.documentElement.classList.toggle('dark');
            document.body.classList.toggle('dark');
            
            const icon = document.getElementById('theme-icon');
            icon.textContent = isDark ? '☀️' : '🌙';
            
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', initTheme);
        
        function showTab(tab) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id$="-tab"]').forEach(el => {
                el.classList.remove('btn-primary');
                el.classList.add('btn-secondary');
            });
            
            // Show selected tab
            document.getElementById(tab + '-content').classList.remove('hidden');
            document.getElementById(tab + '-tab').classList.remove('btn-secondary');
            document.getElementById(tab + '-tab').classList.add('btn-primary');
            
            currentTab = tab;
        }
        
        function clearResults() {
            document.getElementById('simulation-results').classList.add('hidden');
            document.getElementById('code-generation').classList.add('hidden');
            document.getElementById('code-output').classList.add('hidden');
            document.getElementById('error').classList.add('hidden');
        }
        
        async function executeWithInputs(algorithm, inputs) {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ algorithm, inputs }),
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Execution failed');
            }
            
            // Show simulation results
            document.getElementById('simulation-results').classList.remove('hidden');
            document.getElementById('sim-inputs').textContent = JSON.stringify(result.simulation_results.inputs, null, 2);
            document.getElementById('sim-outputs').textContent = JSON.stringify(result.simulation_results.outputs, null, 2);
            document.getElementById('sim-variables').textContent = JSON.stringify(result.simulation_results.variables, null, 2);
            document.getElementById('input-vars').textContent = result.detected_inputs.join(', ');
            
            // Show code generation section
            document.getElementById('code-generation').classList.remove('hidden');
        }
        
        async function executeAlgorithm() {
            const algorithm = document.getElementById('algorithm').value;
            const inputsText = document.getElementById('inputs').value;
            const errorDiv = document.getElementById('error');
            
            // Hide error
            errorDiv.classList.add('hidden');
            
            try {
                // Parse inputs to proper format
                let inputs = {};
                if (inputsText.trim()) {
                    try {
                        // Try JSON first
                        inputs = JSON.parse(inputsText);
                    } catch {
                        // Try simple format
                        if (inputsText.includes('=')) {
                            // n=5,m=6 format
                            const pairs = inputsText.split(',');
                            pairs.forEach(pair => {
                                const [key, value] = pair.split('=');
                                if (key && value) {
                                    inputs[key.trim()] = parseInt(value.trim());
                                }
                            });
                        } else {
                            // Simple number format - detect variables from algorithm first
                            const values = inputsText.split(',').map(v => parseInt(v.trim()));
                            
                            // Call API to detect variables first
                            fetch('/api/detect-variables', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ algorithm }),
                            })
                            .then(resp => resp.json())
                            .then(varResult => {
                                const detectedVars = varResult.variables || [];
                                values.forEach((val, i) => {
                                    if (i < detectedVars.length) {
                                        inputs[detectedVars[i]] = val;
                                    }
                                });
                                
                                // Now execute with proper inputs
                                executeWithInputs(algorithm, inputs);
                            })
                            .catch(() => {
                                // Fallback to default variable names
                                const varNames = ['n', 'm', 'a', 'b', 'x', 'y'];
                                values.forEach((val, i) => {
                                    if (i < varNames.length) {
                                        inputs[varNames[i]] = val;
                                    }
                                });
                                
                                executeWithInputs(algorithm, inputs);
                            });
                            return; // Exit early since we're in async chain
                        }
                    }
                }
                
                // Execute with inputs (either parsed or empty)
                await executeWithInputs(algorithm, inputs);
                showNotification('Algorithm executed successfully!', 'success');
                
            } catch (error) {
                errorDiv.textContent = error.message;
                errorDiv.classList.remove('hidden');
                showNotification('Execution failed: ' + error.message, 'error');
            }
        }
        
        async function generateCode() {
            const target = document.querySelector('input[name="target"]:checked').value;
            
            try {
                showNotification('Generating code...', 'success', 2000);
                
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ target }),
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Code generation failed');
                }
                
                // Show code output section
                document.getElementById('code-output').classList.remove('hidden');
                
                // Update code content
                document.getElementById('python-code').textContent = result.python_code || '// No Python code generated';
                document.getElementById('cpp-code').textContent = result.cpp_code || '// No C++ code generated';
                
                // Show appropriate tab based on target
                if (target === 'python') {
                    showTab('python');
                } else if (target === 'cpp') {
                    showTab('cpp');
                } else {
                    showTab('python'); // Default to python for 'both'
                }
                
                showNotification('Code generated successfully!', 'success');
                
            } catch (error) {
                showNotification('Code generation failed: ' + error.message, 'error');
            }
        }
        
        async function detectVariables() {
            const algorithm = document.getElementById('algorithm').value;
            
            try {
                const response = await fetch('/api/detect-variables', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ algorithm }),
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Variable detection failed');
                }
                
                // Update input placeholder with detected variables
                const inputField = document.getElementById('inputs');
                const vars = result.variables || [];
                if (vars.length > 0) {
                    if (vars.length === 1) {
                        inputField.placeholder = `e.g., ${vars[0]}=5 or 5`;
                    } else {
                        const examples = vars.map((v, i) => `${v}=${i + 2}`).join(', ');
                        inputField.placeholder = `e.g., ${examples} or ${vars.map((v, i) => i + 2).join(',')}`;
                    }
                }
                
            } catch (error) {
                console.error('Variable detection failed:', error);
            }
        }
        
        // Auto-detect variables when algorithm changes
        document.addEventListener('DOMContentLoaded', () => {
            const algorithmTextarea = document.getElementById('algorithm');
            algorithmTextarea.addEventListener('input', detectVariables);
            
            // Initial variable detection
            detectVariables();
        });
    </script>
</body>
</html>
    """
    return html_content

def application(environ, start_response):
    """WSGI application for production deployment"""
    # Create a handler instance
    handler = Algo2CodeHandler
    
    # Simulate HTTP request
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Set up handler attributes
    handler.path = path
    handler.command = method
    handler.headers = dict()
    
    # Parse headers
    for key, value in environ.items():
        if key.startswith('HTTP_'):
            header_name = key[5:].replace('_', '-').title()
            handler.headers[header_name] = value
    
    # Parse query parameters
    if '?' in path:
        handler.path, handler.query_string = path.split('?', 1)
    else:
        handler.query_string = ''
    
    # Process request
    if method == 'GET':
        if path == '/':
            # Serve main page
            html_content = _get_html_content()
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            return [html_content.encode('utf-8')]
        else:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']
    
    elif method == 'POST':
        # Handle API calls
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
        
        if path == '/api/execute':
            try:
                data = json.loads(post_data)
                algorithm = data.get('algorithm', '')
                inputs = data.get('inputs', {})
                
                # Debug logging
                print(f"DEBUG: Algorithm = {repr(algorithm)}")
                print(f"DEBUG: Raw inputs = {repr(inputs)}")
                print(f"DEBUG: Inputs type = {type(inputs)}")
                
                # Fix escaped newlines - handle both literal and JSON escapes
                algorithm = algorithm.replace('\\\\n', '\n').replace('\\\\r', '\r').replace('\\\\t', '\t')
                algorithm = algorithm.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
                
                if not algorithm.strip():
                    start_response('400 Bad Request', [('Content-Type', 'application/json')])
                    return [json.dumps({"error": "Algorithm cannot be empty"}).encode('utf-8')]
                
                # Parse inputs - support multiple formats
                raw_inputs = inputs
                
                # Handle if inputs is already a dict (from JSON)
                if isinstance(raw_inputs, dict):
                    inputs = raw_inputs
                elif isinstance(raw_inputs, (int, float)):
                    # Single numeric value - detect variable name from algorithm
                    var_name = _detect_first_input_variable(algorithm) or 'n'
                    inputs = {var_name: raw_inputs}
                elif isinstance(raw_inputs, str) and raw_inputs.strip():
                    inputs_text = raw_inputs.strip()
                    try:
                        # Try JSON first
                        inputs = json.loads(inputs_text)
                    except:
                        try:
                            # Simple format: "n=5,m=6" or "5,6"
                            if '=' in inputs_text:
                                # n=5,m=6 format
                                pairs = inputs_text.split(',')
                                for pair in pairs:
                                    if '=' in pair:
                                        key, value = pair.split('=', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        # Try to convert to int, fallback to float, then string
                                        try:
                                            inputs[key] = int(value)
                                        except ValueError:
                                            try:
                                                inputs[key] = float(value)
                                            except ValueError:
                                                inputs[key] = value
                            else:
                                # Auto-detect variables from algorithm
                                detected_vars = _detect_input_variables(algorithm)
                                values = [x.strip() for x in inputs_text.split(',')]
                                print(f"DEBUG: Detected vars = {detected_vars}")
                                print(f"DEBUG: Values = {values}")
                                for i, val in enumerate(values):
                                    if i < len(detected_vars):
                                        var_name = detected_vars[i]
                                        # Try to convert to int, fallback to float, then string
                                        try:
                                            inputs[var_name] = int(val)
                                        except ValueError:
                                            try:
                                                inputs[var_name] = float(val)
                                            except ValueError:
                                                inputs[var_name] = val
                        except Exception as e:
                            print(f"Input parsing error: {e}")
                            inputs = {}
                
                print(f"DEBUG: Final inputs = {inputs}")
                
                # Run only Section 1 (simulation)
                from src.lexer import Lexer
                from src.parser import Parser  
                from src.interpreter import Interpreter
                from src.serializer import serialize_result
                
                try:
                    # Lexer
                    lexer = Lexer(algorithm)
                    tokens = lexer.tokenize()
                    
                    # Parser
                    parser = Parser(tokens)
                    ast = parser.parse()
                    
                    # Interpreter
                    interpreter = Interpreter()
                    # Ensure inputs is always a dict
                    if not inputs:
                        inputs = {}
                    elif isinstance(inputs, (int, float)):
                        # Single value - detect variable name from algorithm
                        var_name = _detect_first_input_variable(algorithm) or 'n'
                        inputs = {var_name: inputs}
                    elif isinstance(inputs, str):
                        # Already processed string to dict above
                        pass  # inputs is already a dict
                    # Now inputs should be a dict
                    interpreter.set_inputs(inputs)
                    interpreter.execute(ast)
                    result = interpreter.execution_result
                    
                    # Save result
                    payload = serialize_result(ast, result, algorithm)
                    with open("section1_output.json", 'w', encoding='utf-8') as fh:
                        json.dump(payload, fh, indent=2)
                    
                    # Detect input variables (using the helper method)
                    detected_vars = _detect_input_variables(algorithm)
                    
                    # Send response
                    response_data = {
                        "success": True,
                        "simulation_results": {
                            "inputs": result.get('inputs', {}),
                            "outputs": result.get('outputs', []),
                            "variables": result.get('variables', {})
                        },
                        "detected_inputs": detected_vars
                    }
                    
                    print(f"DEBUG: Response data = {response_data}")
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    return [json.dumps(response_data).encode('utf-8')]
                    
                except Exception as e:
                    print(f"DEBUG: Execution error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
                    return [json.dumps({"error": f"Execution error: {str(e)}"}).encode('utf-8')]
                    
            except json.JSONDecodeError:
                start_response('400 Bad Request', [('Content-Type', 'application/json')])
                return [json.dumps({"error": "Invalid JSON in request body"}).encode('utf-8')]
            except Exception as e:
                print(f"DEBUG: Server error: {str(e)}")
                import traceback
                traceback.print_exc()
                start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
                return [json.dumps({"error": f"Server error: {str(e)}"}).encode('utf-8')]
        
        elif path == '/api/generate':
            try:
                data = json.loads(post_data)
                target = data.get('target', 'both')
                
                # Load AST and generate code
                with open('section1_output.json', 'r') as f:
                    json_data = json.load(f)
                
                from nodes.main_codegen import generate_python, generate_cpp
                from section2.ast_traverser import ASTTraverser
                from section2.rule_engine import RuleEngine
                
                ast_root = json_data.get('ast', {})
                
                # Generate Python
                python_code = ''
                if target in ['python', 'both']:
                    engine = RuleEngine(os.path.join(os.path.dirname(__file__), 'section2/rules/python_rules.l'))
                    traverser = ASTTraverser(engine)
                    lines = traverser.traverse(ast_root, level=0)
                    python_code = '\n'.join(lines) + '\n'
                
                # Generate C++
                cpp_code = ''
                if target in ['cpp', 'both']:
                    engine = RuleEngine(os.path.join(os.path.dirname(__file__), 'section2/rules/cpp_rules.l'))
                    traverser = ASTTraverser(engine)
                    lines = traverser.traverse(ast_root, level=1)
                    cpp_code = '\n'.join(lines) + '\n'
                
                response_data = {
                    'success': True,
                    'python_code': python_code,
                    'cpp_code': cpp_code
                }
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [json.dumps(response_data).encode('utf-8')]
                
            except Exception as e:
                start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
                return [json.dumps({'success': False, 'error': str(e)}).encode('utf-8')]
        
        elif path == '/api/detect-variables':
            try:
                data = json.loads(post_data)
                algorithm = data.get('algorithm', '')
                
                # Simple variable detection
                variables = []
                lines = algorithm.split('\n')
                for line in lines:
                    line = line.strip().upper()
                    if line.startswith('READ'):
                        parts = line.split()
                        if len(parts) > 1:
                            variables.append(parts[1])
                
                response_data = {
                    'success': True,
                    'variables': variables
                }
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [json.dumps(response_data).encode('utf-8')]
                
            except Exception as e:
                start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
                return [json.dumps({'success': False, 'error': str(e)}).encode('utf-8')]
        
        else:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found']
    
    else:
        start_response('405 Method Not Allowed', [('Content-Type', 'text/plain')])
        return [b'Method Not Allowed']

if __name__ == "__main__":
    run_server()

# Alias for gunicorn/Render deployment
app = application
