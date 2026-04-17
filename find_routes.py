# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-backend\app\api\v1\endpoints\system.py', 'r', encoding='utf-8-sig')
c = f.read()
f.close()
# Find all functions
import re
funcs = re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"\)', c)
for method, path in funcs:
    if 'config' in path.lower() or 'ai' in path.lower() or 'model' in path.lower():
        print(f'{method} {path}')