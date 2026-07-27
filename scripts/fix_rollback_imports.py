from pathlib import Path

path = Path("src/deepseek_runtime/security.py")
text = path.read_text(encoding="utf-8")
text = text.replace("import difflib  #", "import base64\nimport difflib  #", 1)
text = text.replace("import subprocess  #", "import stat\nimport subprocess  #", 1)
path.write_text(text, encoding="utf-8")
Path(__file__).unlink()
