# -*- coding: utf-8 -*-
path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

changes = []

# 1. Add attachment state
target1 = "const inputMessage = ref('')"
replacement1 = """const inputMessage = ref('')
const attachments = ref<any[]>([])
const uploadingAttachment = ref(false)"""
if target1 in content and 'attachments = ref' not in content:
    content = content.replace(target1, replacement1)
    changes.append("added attachment state")

# 2. Add upload function before handleSend
target2 = "async function handleSend() {"
replacement2 = """async function uploadAttachment(file: File) {
  uploadingAttachment.value = true
  try {
    const res: any = await (window as any).fetch('/api/v1/local-ai/process-attachment', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: (() => {
        const form = new FormData()
        form.append('file', file)
        form.append('operations', JSON.stringify(['ocr', 'segment', 'keywords']))
        return form
      })()
    })
    const json = await res.json()
    if (json.success) {
      attachments.value.push({
        id: Date.now(),
        name: file.name,
        type: file.type,
        size: file.size,
        text: json.content_text || json.results?.ocr?.text || '',
        keywords: json.results?.keywords?.keywords || [],
        summary: json.results?.summary?.summary || '',
        status: 'ready'
      })
      ElMessage.success(`附件「${file.name}」已解析`)
    } else {
      ElMessage.error('附件解析失败: ' + json.message)
    }
  } catch (e: any) { ElMessage.error('附件解析失败: ' + e.message) }
  finally { uploadingAttachment.value = false }
}

function removeAttachment(id: number) {
  attachments.value = attachments.value.filter(a => a.id !== id)
}

async function handleSend() {"""
if target2 in content and 'uploadAttachment' not in content:
    content = content.replace(target2, replacement2)
    changes.append("added upload function")

# 3. Modify send logic
target3 = "await aiStore.sendMessage(inputMessage.value)\n    inputMessage.value = ''"
replacement3 = """let message = inputMessage.value
    if (attachments.value.length > 0) {
      const attachmentInfo = attachments.value.map(a => {
        let info = `[附件: ${a.name}]`
        if (a.text) info += `\\n提取文字: ${a.text.substring(0, 300)}${a.text.length > 300 ? '...' : ''}`
        if (a.keywords?.length) info += `\\n关键词: ${a.keywords.slice(0, 5).map((k: any) => k.word).join(', ')}`
        return info
      }).join('\\n\\n')
      message = `${message}\\n\\n${attachmentInfo}`
    }
    await aiStore.sendMessage(message)
    inputMessage.value = ''
    attachments.value = []"""
if target3 in content:
    content = content.replace(target3, replacement3)
    changes.append("modified send logic")

# 4. Add attachment list before textarea
target4 = '<el-input\n        v-model="inputMessage"\n        type="textarea"'
replacement4 = """<div v-if="attachments.length > 0" class="attachment-list">
        <div v-for="att in attachments" :key="att.id" class="attachment-item">
          <el-icon><Document /></el-icon>
          <span class="att-name">{{ att.name }}</span>
          <el-tag v-if="att.text" size="small" type="success">已OCR</el-tag>
          <el-button size="small" text type="danger" @click="removeAttachment(att.id)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <el-input
        v-model="inputMessage"
        type="textarea""""
if target4 in content and 'attachment-list' not in content:
    content = content.replace(target4, replacement4)
    changes.append("added attachment list")

# 5. Add upload button before send button
target5 = "<el-button \n        type=\"primary\" \n        :disabled=\"!inputMessage.trim() || aiStore.loading\"\n        @click=\"handleSend\"\n      >"
replacement5 = """<el-upload
        :show-file-list="false"
        :auto-upload="false"
        accept=".jpg,.jpeg,.png,.gif,.bmp,.pdf,.txt,.doc,.docx,.xls,.xlsx,.csv"
        :on-change="(f: any) => uploadAttachment(f.raw || f)"
      >
        <el-button :loading="uploadingAttachment" :disabled="aiStore.loading">
          <el-icon><Upload /></el-icon>
        </el-button>
      </el-upload>
      <el-button
        type="primary"
        :disabled="(!inputMessage.trim() && attachments.length === 0) || aiStore.loading"
        @click="handleSend"
      >"""
if target5 in content and 'el-upload' not in content:
    content = content.replace(target5, replacement5)
    changes.append("added upload button")

# 6. Add styles
target6 = ".chat-input {\n  padding: 12px;"
replacement6 = """.attachment-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.attachment-item { display: flex; align-items: center; gap: 4px; padding: 3px 8px; background: #f0f9eb; border: 1px solid #b3e19d; border-radius: 4px; font-size: 12px; }
.att-name { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-input {
  padding: 12px;"""
if target6 in content and 'attachment-list' not in content:
    content = content.replace(target6, replacement6)
    changes.append("added styles")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Changes:", changes)
print("Done")
