# -*- coding: utf-8 -*-
path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

changes = []

# 1. Add attachment state
if 'attachments = ref' not in content:
    content = content.replace(
        "const inputMessage = ref('')",
        "const inputMessage = ref('')\nconst attachments = ref([])\nconst uploadingAttachment = ref(false)"
    )
    changes.append("attachment state")

# 2. Add upload function before handleSend
if 'uploadAttachment' not in content:
    upload_fn = """
async function uploadAttachment(file: File) {
  uploadingAttachment.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('operations', JSON.stringify(['ocr', 'segment', 'keywords']))
    const res: any = await (window as any).fetch('/api/v1/local-ai/process-attachment', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: form
    })
    const json = await res.json()
    if (json.success) {
      attachments.value.push({
        id: Date.now(), name: file.name, type: file.type, size: file.size,
        text: json.content_text || (json.results && json.results.ocr && json.results.ocr.text) || '',
        keywords: (json.results && json.results.keywords && json.results.keywords.keywords) || [],
        status: 'ready'
      })
      ElMessage.success('附件「' + file.name + '」已解析')
    } else {
      ElMessage.error('解析失败: ' + json.message)
    }
  } catch (e: any) { ElMessage.error('解析失败: ' + e.message) }
  finally { uploadingAttachment.value = false }
}

function removeAttachment(id: number) {
  attachments.value = attachments.value.filter((a: any) => a.id !== id)
}
"""
    content = content.replace(
        "async function handleSend() {",
        upload_fn + "async function handleSend() {"
    )
    changes.append("upload function")

# 3. Modify send to include attachments
if "inputMessage.value = ''\n\n    // 滚动" in content:
    old_scroll = "inputMessage.value = ''\n\n    // 滚动"
    new_scroll = """inputMessage.value = ''
    // 清空附件
    if (attachments.value.length > 0) {
      const attTexts = attachments.value.map((a: any) => {
        let t = '[附件: ' + a.name + ']'
        if (a.text) t += '\\n内容: ' + a.text.substring(0, 300)
        if (a.keywords && a.keywords.length) t += '\\n关键词: ' + a.keywords.slice(0, 5).map((k: any) => k.word).join(', ')
        return t
      }).join('\\n\\n')
      // Attach to last user message
    }
    attachments.value = []

    // 滚动"""
    content = content.replace(old_scroll, new_scroll)
    changes.append("attachment cleanup")

# 4. Add attachment list in template
if 'attachment-list' not in content:
    old_input_area = '        @keydown.enter.ctrl="handleSend"'
    new_input_area = """        @keydown.enter.ctrl="handleSend"
      />
      <!-- 附件列表 -->
      <div v-if="attachments.length > 0" class="attachment-list">
        <div v-for="att in attachments" :key="att.id" class="attachment-item">
          <el-icon><Document /></el-icon>
          <span>{{ att.name }}</span>
          <el-tag v-if="att.text" size="small" type="success">已解析</el-tag>
          <el-button size="small" text @click="removeAttachment(att.id)"><el-icon><Close /></el-icon></el-button>
        </div>
      </div>
      <el-input"""
    if old_input_area in content:
        content = content.replace(old_input_area, new_input_area)
        changes.append("attachment list")

# 5. Add upload button before send
if 'el-upload' not in content:
    old_send_btn = 'type="primary" \n        :disabled="!inputMessage'
    new_send_btn = '''<el-upload
        :show-file-list="false"
        :auto-upload="false"
        accept=".jpg,.jpeg,.png,.gif,.bmp,.pdf,.txt,.doc,.docx,.xls,.xlsx,.csv"
        :on-change="(f: any) => uploadAttachment(f.raw || f)"
      >
        <el-button :disabled="aiStore.loading"><el-icon><Upload /></el-icon></el-button>
      </el-upload>
      <el-button
        type="primary"
        :disabled="(!inputMessage.trim() && attachments.length === 0) || aiStore.loading"'''
    if old_send_btn in content:
        content = content.replace(old_send_btn, new_send_btn)
        changes.append("upload button")

# 6. Add styles
if '.attachment-list' not in content:
    old_chat_input = '.chat-input {'
    new_chat_input = """.attachment-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.attachment-item { display: flex; align-items: center; gap: 4px; padding: 3px 8px; background: #f0f9eb; border: 1px solid #b3e19d; border-radius: 4px; font-size: 12px; }
.chat-input {"""
    content = content.replace(old_chat_input, new_chat_input)
    changes.append("styles")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Changes:", changes)
print("Done. Size:", len(content))
