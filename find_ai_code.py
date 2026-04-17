# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Find AI helper related code
ai_pos = c.find('AI 设计')
if ai_pos > 0:
    print("Found 'AI 设计' at position", ai_pos)
    
# Find generateWithAI function
gen_pos = c.find('function generateWithAI')
if gen_pos > 0:
    # Get the function content
    end = c.find('async function', gen_pos + 20)
    if end < 0:
        end = c.find('function ', gen_pos + 20)
    if end < 0:
        end = c.find('onMounted', gen_pos + 20)
    print("\ngenerateWithAI function:")
    print(c[gen_pos:end][:2000])