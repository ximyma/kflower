# -*- coding: utf-8 -*-
"""
Add AI config entry to AIChatDialog
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 添加 Setting 和 Warning 图标导入
old_icons = "import { ref, nextTick, computed } from 'vue'"
new_icons = "import { ref, nextTick, computed } from 'vue'\nimport { useRouter } from 'vue-router'"

if old_icons in content:
    content = content.replace(old_icons, new_icons)
    print('Added router import')

# 2. 添加 router
old_emit = "const emit = defineEmits(['close'])\nconst aiStore = useAIStore()"
new_emit = "const emit = defineEmits(['close'])\nconst aiStore = useAIStore()\nconst router = useRouter()"

if old_emit in content:
    content = content.replace(old_emit, new_emit)
    print('Added router instance')

# 3. 添加跳转到设置页面的函数
old_types = '''// AI类型选项
const aiTypes = ['''
new_types = '''// 跳转到 AI 设置
function goToAISettings() {
  emit('close')
  router.push('/settings?tab=ai')
}

// AI类型选项
const aiTypes = ['''

if old_types in content:
    content = content.replace(old_types, new_types)
    print('Added goToAISettings function')

# 4. 在头部添加设置按钮
old_header = '''<el-button 
          type="danger" 
          size="small" 
          text
          @click="aiStore.clearMessages"
        >
          <el-icon><Delete /></el-icon>
        </el-button>'''

new_header = '''<el-button 
          size="small" 
          text
          @click="goToAISettings"
          title="AI 配置"
        >
          <el-icon><Setting /></el-icon>
        </el-button>
        <el-button 
          type="danger" 
          size="small" 
          text
          @click="aiStore.clearMessages"
        >
          <el-icon><Delete /></el-icon>
        </el-button>'''

if old_header in content:
    content = content.replace(old_header, new_header)
    print('Added settings button in header')

# 5. 添加 Setting 图标到 imports
if 'Setting' not in content:
    content = content.replace('MagicStick /></el-icon>', 'MagicStick /></el-icon>\n        <el-icon v-else-if="msg.role === \'assistant\'" :size="20"><Setting /></el-icon>')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done: AIChatDialog updated')
