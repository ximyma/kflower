# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-backend\app\api\v1\endpoints\system.py', 'r', encoding='utf-8-sig')
c = f.read()
f.close()
funcs = re.findall(r'async def (\w+)\(', c)
print('Functions:', funcs)
prefixes = re.findall(r'prefix=["\']([^"\']+)["\']', c)
print('Prefixes:', prefixes)