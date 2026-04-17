# -*- coding: utf-8 -*-
"""Fix api/index.ts: allow timeout override for AI chat calls"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\api\index.ts'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix 1: aiAPI.chat - add timeout support
old_ai = """export const aiAPI = {
  chat: (data: { 
    message: string; 
    conversation_id?: string; 
    ai_type?: string;
    related_type?: string;
    related_id?: number;
  }) => api.post('/ai/chat', data),"""

new_ai = """export const aiAPI = {
  chat: (data: { 
    message: string; 
    conversation_id?: string; 
    ai_type?: string;
    related_type?: string;
    related_id?: number;
  }, config?: AxiosRequestConfig) => api.post('/ai/chat', data, config),"""

count1 = content.count(old_ai)
print(f"aiAPI.chat: found {count1}")
if count1 == 1:
    content = content.replace(old_ai, new_ai)
    print("  [OK] aiAPI.chat supports timeout override")

# Fix 2: agentAPI.chat - add timeout support
old_agent = """export const agentAPI = {
  chat: (data: {
    message: string;
    conversation_id?: string;
    use_rag?: boolean;
    enable_tools?: boolean;
  }) => api.post('/agent/chat', data),"""

new_agent = """export const agentAPI = {
  chat: (data: {
    message: string;
    conversation_id?: string;
    use_rag?: boolean;
    enable_tools?: boolean;
  }, config?: AxiosRequestConfig) => api.post('/agent/chat', data, config),"""

count2 = content.count(old_agent)
print(f"agentAPI.chat: found {count2}")
if count2 == 1:
    content = content.replace(old_agent, new_agent)
    print("  [OK] agentAPI.chat supports timeout override")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\napi/index.ts updated!")
