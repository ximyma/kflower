# -*- coding: utf-8 -*-
"""Fix AIChatDialog.vue: clear input BEFORE sending (not after await)"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old = """async function handleSend() {
  const hasContent = inputMessage.value.trim() || attachments.value.length > 0
  if (!hasContent || aiStore.loading) return

  let message = inputMessage.value.trim()

  // 附加文件内容
  if (attachments.value.length > 0) {
    const parts = attachments.value.map((a: any) => {
      let part = `[附件: ${a.name}]`
      if (a.text) {
        part += `\n内容摘要: ${a.text.substring(0, 500)}${a.text.length > 500 ? '...' : ''}`
      }
      if (a.keywords?.length) {
        const kws = a.keywords.slice(0, 10).map((k: any) => k.word || k).join(', ')
        part += `\n关键词: ${kws}`
      }
      return part
    })
    message = message ? `${message}\n\n${parts.join('\n\n')}` : parts.join('\n\n')
  }

  await aiStore.sendMessage(message)
  inputMessage.value = ''
  attachments.value = []
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}"""

new = """async function handleSend() {
  const hasContent = inputMessage.value.trim() || attachments.value.length > 0
  if (!hasContent || aiStore.loading) return

  let message = inputMessage.value.trim()

  // 附加文件内容
  if (attachments.value.length > 0) {
    const parts = attachments.value.map((a: any) => {
      let part = `[附件: ${a.name}]`
      if (a.text) {
        part += `\\n内容摘要: ${a.text.substring(0, 500)}${a.text.length > 500 ? '...' : ''}`
      }
      if (a.keywords?.length) {
        const kws = a.keywords.slice(0, 10).map((k: any) => k.word || k).join(', ')
        part += `\\n关键词: ${kws}`
      }
      return part
    })
    message = message ? `${message}\\n\\n${parts.join('\\n\\n')}` : parts.join('\\n\\n')
  }

  // 立即清空输入框和附件，不等AI回复
  inputMessage.value = ''
  attachments.value = []

  // 异步发送，不阻塞UI
  aiStore.sendMessage(message)
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}"""

count = content.count(old)
print(f"Found {count} occurrences")
if count == 1:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("[OK] Fixed: input cleared immediately before AI response")
else:
    print("[ERROR] Could not find exact match")
