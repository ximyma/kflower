# -*- coding: utf-8 -*-
"""
Enhance AIChatDialog with file upload support
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 添加 Upload 图标
if 'Upload,' not in content:
    content = content.replace(
        "import { ref, nextTick, computed } from 'vue'",
        "import { ref, nextTick, computed } from 'vue'"
    )

# 2. 添加附件相关状态
old_store = "const inputMessage = ref('')"
new_store = """const inputMessage = ref('')
const attachments = ref<any[]>([])
const uploadingAttachment = ref(false)"""

if old_store in content:
    content = content.replace(old_store, new_store)
    print("Added attachment state")

# 3. 添加上传附件函数
old_send = "async function handleSend() {"
new_send = """async function uploadAttachment(file: File) {
  uploadingAttachment.value = true
  try {
    const res: any = await (window as any).fetch('/api/v1/local-ai/process-attachment', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + (localStorage.getItem('kflower_token') || ''),
      },
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
  } catch (e: any) {
    ElMessage.error('附件解析失败: ' + e.message)
  } finally {
    uploadingAttachment.value = false
  }
}

function removeAttachment(id: number) {
  attachments.value = attachments.value.filter(a => a.id !== id)
}

async function handleSend() {"""

if old_send in content:
    content = content.replace(old_send, new_send)
    print("Added uploadAttachment function")

# 4. 修改发送逻辑，附加文件内容
old_send_logic = "await aiStore.sendMessage(inputMessage.value)"
new_send_logic = """// 构建带附件的消息
    let message = inputMessage.value
    if (attachments.value.length > 0) {
      const attachmentInfo = attachments.value.map(a => {
        let info = `[附件: ${a.name}]`
        if (a.text) info += `\\n内容: ${a.text.substring(0, 200)}${a.text.length > 200 ? '...' : ''}`
        if (a.keywords?.length) info += `\\n关键词: ${a.keywords.slice(0, 5).map((k: any) => k.word).join(', ')}`
        return info
      }).join('\\n\\n')
      message = `${message}\\n\\n${attachmentInfo}`
    }
    await aiStore.sendMessage(message)
    inputMessage.value = ''
    attachments.value = []"""

if old_send_logic in content:
    content = content.replace(old_send_logic, new_send_logic)
    print("Updated send logic with attachments")

# 5. 添加附件上传区域到输入框上方
old_input = '''<el-input
        v-model="inputMessage"
        type="textarea"
        :rows="2"
        placeholder="输入您的问题..."'''

new_input = '''<!-- 附件列表 -->
      <div v-if="attachments.length > 0" class="attachment-list">
        <div v-for="att in attachments" :key="att.id" class="attachment-item">
          <el-icon><Document /></el-icon>
          <span class="att-name">{{ att.name }}</span>
          <el-tag v-if="att.text" size="small" type="success">已OCR</el-tag>
          <el-button size="small" text type="danger" @click="removeAttachment(att.id)"><el-icon><Close /></el-icon></el-button>
        </div>
      </div>

      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="2"
        placeholder="输入您的问题，或上传图片/文档作为附件..."'''

if old_input in content:
    content = content.replace(old_input, new_input)
    print("Added attachment list to UI")

# 6. 在发送按钮旁添加上传按钮
old_button = '<el-button \n        type="primary" \n        :disabled="!inputMessage.trim() || aiStore.loading"\n        @click="handleSend"'
new_button = '''<el-upload
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
        @click="handleSend"'''

if old_button in content:
    content = content.replace(old_button, new_button)
    print("Added upload button")

# 7. 添加附件样式
old_style = '.chat-input {'
new_style = '''.attachment-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.attachment-item { display: flex; align-items: center; gap: 6px; padding: 4px 10px; background: #f0f9eb; border: 1px solid #b3e19d; border-radius: 4px; font-size: 12px; }
.att-name { max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-input {'''

if old_style in content:
    content = content.replace(old_style, new_style)
    print("Added attachment styles")

# 8. 添加 Upload 图标
if 'Upload' not in content or 'UploadIcon' not in content:
    # 在 import 中添加 Upload
    import_line = "import { useRouter } from 'vue-router'"
    if import_line in content and 'Upload' not in content:
        # Upload 已经通过 el-upload 自动可用，这里不需要额外导入

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("Done: AIChatDialog enhanced with attachments")
