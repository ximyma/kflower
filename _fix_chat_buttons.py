# -*- coding: utf-8 -*-
"""Fix AIChatDialog.vue header buttons visibility - high contrast on gradient background"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix header actions section - replace all text buttons with high-contrast versions
old = '''      <div class="header-actions">
        <el-select v-model="aiStore.aiType" size="small" style="width:100px" @change="aiStore.setAIType">
          <el-option value="general" label="智能助手" />
          <el-option value="template" label="模板设计" />
          <el-option value="workflow" label="流程审批" />
          <el-option value="analytics" label="决策分析" />
        </el-select>
        <el-select v-model="selectedModelId" size="small" style="width:150px" @change="handleModelChange">
          <el-option v-for="model in aiStore.models" :key="model.modelId" :label="model.modelName || model.modelId" :value="model.modelId">
            <span>{{ model.modelName || model.modelId }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
          </el-option>
        </el-select>
        <el-button size="small" text @click="goToSettings" title="AI配置">
          <el-icon><Setting /></el-icon>
        </el-button>
        <el-button size="small" text @click="aiStore.clearMessages">
          <el-icon><Delete /></el-icon>
        </el-button>
        <el-button size="small" type="danger" circle @click="emit('close')" title="关闭">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>'''

new = '''      <div class="header-actions">
        <el-select v-model="aiStore.aiType" size="small" class="header-select" @change="aiStore.setAIType">
          <el-option value="general" label="智能助手" />
          <el-option value="template" label="模板设计" />
          <el-option value="workflow" label="流程审批" />
          <el-option value="analytics" label="决策分析" />
        </el-select>
        <el-select v-model="selectedModelId" size="small" class="header-select header-select-wide" @change="handleModelChange" placeholder="选择模型">
          <el-option v-for="model in aiStore.models" :key="model.modelId" :label="model.modelName || model.modelId" :value="model.modelId">
            <span>{{ model.modelName || model.modelId }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
          </el-option>
        </el-select>
        <button class="header-icon-btn" @click="goToSettings" title="AI配置">
          <el-icon :size="16"><Setting /></el-icon>
        </button>
        <button class="header-icon-btn" @click="aiStore.clearMessages" title="清空对话">
          <el-icon :size="16"><Delete /></el-icon>
        </button>
        <button class="header-close-btn" @click="emit('close')" title="关闭">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </div>'''

count = content.count(old)
print(f"Found {count} occurrences of header-actions")

if count == 1:
    content = content.replace(old, new)
    
    # Add styles for the new buttons - append before </style>
    style_add = '''
/* Header buttons - high contrast on gradient */
.header-select { width: 100px; }
.header-select-wide { width: 140px; }
.header-select :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.15) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255,255,255,0.3) !important;
}
.header-select :deep(.el-input__inner) {
  color: #fff !important;
  font-size: 13px;
}
.header-select :deep(.el-input__inner)::placeholder {
  color: rgba(255,255,255,0.6) !important;
}
.header-select :deep(.el-select__caret) {
  color: rgba(255,255,255,0.8) !important;
}
.header-icon-btn {
  width: 32px; height: 32px; border-radius: 6px;
  border: none; cursor: pointer;
  background: rgba(255,255,255,0.15);
  color: #fff; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.header-icon-btn:hover {
  background: rgba(255,255,255,0.3);
}
.header-close-btn {
  width: 32px; height: 32px; border-radius: 6px;
  border: none; cursor: pointer;
  background: rgba(255,71,87,0.8);
  color: #fff; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
  font-size: 16px;
}
.header-close-btn:hover {
  background: #ff4757;
}
'''
    content = content.replace('</style>', style_add + '</style>')
    
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("Fixed! Header buttons now have high contrast on gradient background.")
else:
    print("ERROR: Could not find unique match")
    # Debug
    idx = content.find('header-actions')
    if idx > 0:
        print(content[idx:idx+500])
