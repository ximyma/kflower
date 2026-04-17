# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# AI 对话框结束位置
ai_dialog_end = '</el-dialog>'
pos = content.find('v-model="showAIHelper"')
ai_end_pos = content.find(ai_dialog_end, pos) + len(ai_dialog_end)

# JSON导入对话框插入位置
json_dialog = '''

    <!-- JSON 导入对话框 -->
    <el-dialog v-model="showJsonImport" title="JSON 导入表单" width="680px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px">
        <div style="font-size:13px;color:#666">
          <b>支持的JSON格式：</b>直接粘贴 JSON 数组，每个对象为一个字段定义。
          <br/>字段类型：<code>text</code>/<code>select</code>/<code>date</code>/<code>number</code>/<code>phone</code>/<code>email</code>/<code>radio</code>/<code>checkbox</code>/<code>upload</code>等
        </div>
      </el-alert>
      <el-input
        v-model="jsonInputText"
        type="textarea"
        :rows="12"
        placeholder="粘贴 JSON 内容，示例：&#10;["&#10;  {\\\"type\\\":\\\"text\\\",\\\"label\\\":\\\"客户名称\\\",\\\"name\\\":\\\"customer_name\\\",\\\"required\\\":true,\\\"width\\\":\\\"100%\\\"},"&#10;  {\\\"type\\\":\\\"select\\\",\\\"label\\\":\\\"类型\\\",\\\"name\\\":\\\"type\\\",\\\"options\\\":[\\\"A\\\",\\\"B\\\"]}"&#10;]"
        style="font-family:monospace;font-size:13px"
      />
      <template #footer>
        <el-button @click="showJsonImport = false">取消</el-button>
        <el-button type="primary" @click="importFromJson">导入并生成表单</el-button>
      </template>
    </el-dialog>
'''

# 在AI对话框后、数据表单对话框前插入
target = '\n\n    <!-- 填写数据弹窗 -->'
target_pos = content.find(target, ai_end_pos)

if target_pos > 0:
    content = content[:ai_end_pos] + json_dialog + content[target_pos:]
    print("[OK] JSON导入对话框已插入")
else:
    # 找不到就插在AI对话框后面
    content = content[:ai_end_pos] + json_dialog + content[ai_end_pos:]
    print("[OK] JSON导入对话框已插入（到AI对话框后）")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("完成！")