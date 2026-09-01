import re

with open('app/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

def check_brackets(text):
    stack = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for char in line:
            if char == '{': stack.append(('{', i+1))
            elif char == '(': stack.append(('(', i+1))
            elif char == '[': stack.append(('[', i+1))
            elif char == '}':
                if not stack or stack[-1][0] != '{': print(f"Mismatch at {i+1}: }")
                else: stack.pop()
            elif char == ')':
                if not stack or stack[-1][0] != '(': print(f"Mismatch at {i+1}: )")
                else: stack.pop()
            elif char == ']':
                if not stack or stack[-1][0] != '[': print(f"Mismatch at {i+1}: ]")
                else: stack.pop()
    print("Stack remainder:", stack)
check_brackets(code)
