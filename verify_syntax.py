import jinja2
import os

env = jinja2.Environment()

file_path = r'src/templates/partials/analysis_panel.html'
abs_path = os.path.abspath(file_path)

print(f"Verifying syntax for: {abs_path}")

try:
    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Attempt to parse the template
    env.parse(content)
    print("SUCCESS: Template syntax is valid.")
    print(f"File has {len(content.splitlines())} lines.")

except jinja2.TemplateSyntaxError as e:
    print(f"ERROR: TemplateSyntaxError at line {e.lineno}")
    print(f"Message: {e.message}")
except Exception as e:
    print(f"ERROR: {e}")
