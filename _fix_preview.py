# -*- coding: utf-8 -*-
"""Fix preview dialog to render all field types"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old = '''<el-rate v-else-if="f.type === 'rate'" v-model="previewData[f.name]" />
          <div v-else-if="f.type === 'divider'" style="border-top:1px solid #eee;margin:8px 0"></div>
          <h4 v-else-if="f.type === 'heading'" style="margin:8px 0">{{ f.label }}</h4>
        </el-form-item>'''

new = '''<el-rate v-else-if="f.type === 'rate'" v-model="previewData[f.name]" />
          <el-slider v-else-if="f.type === 'slider'" v-model="previewData[f.name]" style="width:100%" />
          <el-input v-else-if="f.type === 'money'" v-model="previewData[f.name]" placeholder="0.00">
            <template #prepend>¥</template>
          </el-input>
          <el-input v-else-if="f.type === 'password'" type="password" v-model="previewData[f.name]" show-password placeholder="请输入密码" />
          <el-date-picker v-else-if="f.type === 'datetime'" v-model="previewData[f.name]" type="datetime" style="width:100%" />
          <el-time-picker v-else-if="f.type === 'time'" v-model="previewData[f.name]" style="width:100%" />
          <el-date-picker v-else-if="f.type === 'daterange'" v-model="previewData[f.name]" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" style="width:100%" />
          <el-upload v-else-if="f.type === 'upload'" :auto-upload="false" action="#" :limit="5">
            <el-button size="small" type="primary"><el-icon><Upload /></el-icon> 点击上传</el-button>
            <template #tip><div class="el-upload__tip">支持常见文件格式</div></template>
          </el-upload>
          <el-upload v-else-if="f.type === 'image'" :auto-upload="false" action="#" accept="image/*" list-type="picture-card" :limit="3">
            <el-icon><Plus /></el-icon>
          </el-upload>
          <el-input v-else-if="f.type === 'richtext'" type="textarea" :rows="4" v-model="previewData[f.name]" placeholder="富文本内容（预览模式）" />
          <el-input v-else-if="f.type === 'autonum'" disabled :placeholder="'自动生成编号'" />
          <el-input v-else-if="f.type === 'location'" v-model="previewData[f.name]" placeholder="请输入地址" />
          <el-color-picker v-else-if="f.type === 'color'" v-model="previewData[f.name]" />
          <el-input v-else-if="['signature','barcode','qrcode','subform','relation','refdata','user','org','icon','group','grid','tabs','cascader'].includes(f.type)" disabled :placeholder="'[' + f.type + '] ' + f.label" />
          <div v-else-if="f.type === 'divider'" style="border-top:1px solid #eee;margin:8px 0"></div>
          <h4 v-else-if="f.type === 'heading'" style="margin:8px 0">{{ f.label }}</h4>
          <el-input v-else v-model="previewData[f.name]" :placeholder="'[' + f.type + ']'" />
        </el-form-item>'''

count = content.count(old)
print(f"Found {count} occurrences")

if count == 1:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("Fixed preview dialog!")
else:
    print("ERROR: Could not find unique match")
    # Show what's around divider
    idx = content.find("f.type === 'divider'")
    if idx > 0:
        print(content[idx-200:idx+200])
