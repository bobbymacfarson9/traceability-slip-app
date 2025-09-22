import re

def fix_parser_validation():
    """Fix the parser to handle None returns from _create_record"""
    
    # Read the current file
    with open('egg_packing_predictor_universal.py', 'r') as f:
        content = f.read()
    
    # Replace all instances of records.append(_create_record(...)) with proper None handling
    pattern = r'records\.append\(_create_record\(([^)]+)\)\)'
    replacement = r'record = _create_record(\1)\n                if record:\n                    records.append(record)'
    
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open('egg_packing_predictor_universal.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed parser validation")

if __name__ == "__main__":
    fix_parser_validation()
