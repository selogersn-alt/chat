import py_compile
import os
import sys

def check_all_syntax():
    errors = []
    for root, dirs, files in os.walk('.'):
        if '.git' in root or '__pycache__' in root or 'venv' in root or '.venv' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"Syntax Error in {path}:\n{e}")
                except Exception as e:
                    errors.append(f"Error checking {path}: {e}")
    return errors

if __name__ == '__main__':
    errs = check_all_syntax()
    with open('syntax_report.txt', 'w', encoding='utf-8') as f:
        if errs:
            f.write("Syntax errors found:\n" + "\n---\n".join(errs))
        else:
            f.write("All Python files compiled successfully. No syntax errors detected.")
    print("Done")
