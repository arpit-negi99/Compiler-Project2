#!/usr/bin/env python3
"""
Algo2Code Setup Script
Interactive setup and project launcher
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_project_structure():
    """Check if project structure is correct"""
    required_dirs = ['src', 'section2', 'examples']
    required_files = ['unified_main.py', 'final_web_server.py']
    
    missing_dirs = []
    missing_files = []
    
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    for file_name in required_files:
        if not os.path.isfile(file_name):
            missing_files.append(file_name)
    
    if missing_dirs or missing_files:
        print("❌ Project structure check failed:")
        if missing_dirs:
            print(f"   Missing directories: {missing_dirs}")
        if missing_files:
            print(f"   Missing files: {missing_files}")
        return False
    
    print("✅ Project structure check passed")
    return True

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True, cwd=os.getcwd())
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def start_web_server():
    """Start the web server"""
    print("\n🌐 Starting Algo2Code Web Server...")
    print("   Open http://localhost:8000 in your browser")
    print("   Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([sys.executable, "final_web_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start web server: {e}")

def run_cli():
    """Run command line interface"""
    print("\n💻 Algo2Code Command Line Interface")
    
    # Get algorithm source
    print("\nChoose algorithm source:")
    print("1. Use example algorithm")
    print("2. Enter algorithm manually")
    print("3. Load from file")
    
    choice = input("Enter choice (1-3): ").strip()
    
    algorithm_text = ""
    if choice == "1":
        # Use example
        algorithm_text = """READ n
SET sum = 0
FOR i = 1 TO n
    SET sum = sum + i
END
PRINT sum"""
        print("\n📝 Using example algorithm:")
        print(algorithm_text)
        
    elif choice == "2":
        print("\n📝 Enter your algorithm (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "" and len(lines) > 0 and lines[-1] == "":
                break
            lines.append(line)
        algorithm_text = "\n".join(lines[:-1])  # Remove the last empty line
        
    elif choice == "3":
        file_path = input("Enter file path: ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                algorithm_text = f.read()
            print(f"✅ Loaded algorithm from {file_path}")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return
    
    else:
        print("❌ Invalid choice")
        return
    
    # Get inputs
    inputs_str = input("\nEnter inputs (JSON format, optional): ").strip()
    inputs = {}
    if inputs_str:
        try:
            import json
            inputs = json.loads(inputs_str)
        except json.JSONDecodeError:
            print("❌ Invalid JSON format for inputs")
            return
    
    # Run algorithm
    print("\n🚀 Running algorithm...")
    try:
        from unified_main import run_complete_pipeline
        success, python_code, cpp_code = run_complete_pipeline(algorithm_text, inputs)
        
        if success:
            print("✅ Algorithm completed successfully!")
            print("\n📊 Results:")
            if inputs:
                print(f"   Inputs: {inputs}")
            
            # Show generated code
            print("\n🐍 Generated Python Code:")
            print(python_code)
            
            print("\n🚀 Generated C++ Code:")
            print(cpp_code)
            
        else:
            print("❌ Algorithm execution failed")
    
    except Exception as e:
        print(f"❌ Error running algorithm: {e}")

def test_examples():
    """Test with example algorithms"""
    print("\n🧪 Testing Algo2Code with Examples")
    
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print("❌ Examples directory not found")
        return
    
    example_files = list(examples_dir.glob("*.algo"))
    if not example_files:
        print("❌ No example files found")
        return
    
    print(f"📁 Found {len(example_files)} example(s)")
    
    for example_file in example_files:
        print(f"\n🧪 Testing: {example_file.name}")
        try:
            with open(example_file, 'r', encoding='utf-8') as f:
                algorithm_text = f.read()
            
            from unified_main import run_complete_pipeline
            success, python_code, cpp_code = run_complete_pipeline(algorithm_text, {"n": 5})
            
            if success:
                print(f"✅ {example_file.name}: PASSED")
            else:
                print(f"❌ {example_file.name}: FAILED")
        
        except Exception as e:
            print(f"❌ {example_file.name}: ERROR - {e}")

def show_usage():
    """Show usage instructions"""
    print("\n📖 Algo2Code Usage Guide")
    print("=" * 40)
    
    print("\n🌐 Web Interface (Recommended):")
    print("   python final_web_server.py")
    print("   # Open http://localhost:8000")
    
    print("\n💻 Command Line:")
    print("   python unified_main.py --file examples/sum.algo --inputs '{\"n\": 5}'")
    print("   python unified_main.py --text \"READ n\\nPRINT n\" --inputs '{\"n\": 10}'")
    
    print("\n📁 Algorithm Syntax:")
    print("   READ variable_name")
    print("   PRINT expression")
    print("   SET variable = expression")
    print("   FOR variable = start TO end")
    print("   END")
    print("   IF condition")
    print("   ELSE")
    print("   END")
    
    print("\n💡 Input Formats:")
    print("   JSON: {\"n\": 5, \"m\": 10}")
    print("   Simple: 5 (assigns to 'n')")
    print("   Named: n=5,m=10")

def main():
    """Main setup menu"""
    print("🎯 Algo2Code Setup & Launcher")
    print("=" * 40)
    
    # System checks
    print("\n🔍 System Checks:")
    if not check_python_version():
        return
    if not check_project_structure():
        return
    
    # Main menu
    while True:
        print("\n📋 Main Menu:")
        print("1. 🌐 Start Web Server")
        print("2. 💻 Command Line Interface")
        print("3. 🧪 Test Examples")
        print("4. 📖 Usage Guide")
        print("5. 🚪 Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            start_web_server()
        elif choice == "2":
            run_cli()
        elif choice == "3":
            test_examples()
        elif choice == "4":
            show_usage()
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
