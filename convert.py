with open('app/frontend/src/App.jsx', 'r', encoding='utf-16') as f:
    code = f.read()
with open('app/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
