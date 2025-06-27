#!/usr/bin/env python
"""
Script to check lambda_handler.py for syntax errors
"""
import sys
import os

def check_syntax(file_path):
    """Check Python file for syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            source = file.read()
        
        # Compile the source to check for syntax errors
        compile(source, file_path, 'exec')
        print(f"✅ No syntax errors found in {file_path}")
        return True
    except SyntaxError as e:
        line_no = e.lineno
        offset = e.offset
        
        # Get the problematic line and the surrounding context
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Print error details
        print(f"❌ Syntax error found in {file_path} at line {line_no}, position {offset}")
        print(f"Error message: {e}")
        
        # Print the problematic line and some context
        start_line = max(0, line_no - 3)
        end_line = min(len(lines), line_no + 2)
        
        print("\nContext:")
        for i in range(start_line, end_line):
            line_marker = "→" if i+1 == line_no else " "
            print(f"{line_marker} {i+1:4d}: {lines[i].rstrip()}")
        
        # Print a marker under the error position if we have it
        if offset:
            print(f"       {' ' * offset}^")
        
        return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

if __name__ == "__main__":
    file_path = "lambda_handler.py"
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    result = check_syntax(file_path)
    sys.exit(0 if result else 1)
