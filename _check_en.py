# -*- coding: utf-8 -*-
"""Check all Vue files for remaining English UI text"""
import os, re
sys_stdout_reconfigure = True

import sys
sys.stdout.reconfigure(encoding='utf-8')

views_dir = r'D:\kflower\kflower-frontend\src\common\pc\views'
for fname in sorted(os.listdir(views_dir)):
    if not fname.endswith('.vue'):
        continue
    path = os.path.join(views_dir, fname)
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read()
    
    # Find English text in quotes after label/title/placeholder
    pattern = r'(?:label|title|placeholder)\s*=\s*["\x27]([A-Z][a-z]+[^"\x27]*?)["\x27]'
    matches = re.findall(pattern, content)
    if matches:
        print(f'\n{fname}:')
        for m in matches[:15]:
            print(f'  "{m}"')
