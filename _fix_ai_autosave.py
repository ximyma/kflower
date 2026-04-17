# -*- coding: utf-8 -*-
"""
Enhance AI generate - ask to save directly after generation
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 generateWithAI 函数中生成字段后的部分，添加自动保存逻辑
# 现在的逻辑：生成后切换到设计器，提示用户保存
# 改进：生成后自动调用保存模板 API

# 查找需要修改的代码块
old_block = '''    showAIHelper.value = false; aiPrompt.value = ''
    // 自动切换到设计器视图
    if (viewMode.value === 'list') { viewMode.value = 'design' }
  } catch { ElMessage.error('AI生成失败') }
  finally { aiLoading.value = false }
}'''

new_block = '''    showAIHelper.value = false; aiPrompt.value = ''
    // 自动切换到设计器视图
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    // 自动保存模板
    await saveTemplate()
  } catch { ElMessage.error('AI生成失败') }
  finally { aiLoading.value = false }
}'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('Enhanced: AI 生成后自动保存')
elif 'await saveTemplate()' in content:
    print('Already has auto save')
else:
    # 找一个更灵活的方式
    # 在 finally 前面插入 await saveTemplate()
    old_finally = "  } catch { ElMessage.error('AI生成失败') }\n  finally { aiLoading.value = false }"
    new_finally = "    // 自动保存模板\n    await saveTemplate()\n  } catch { ElMessage.error('AI生成失败') }\n  finally { aiLoading.value = false }"
    if old_finally in content:
        content = content.replace(old_finally, new_finally)
        print('Enhanced: 添加了自动保存调用')
    else:
        print('Pattern not found, checking code...')
        idx = content.find("ElMessage.error('AI生成失败')")
        if idx > 0:
            print(f'Found error message at {idx}')
            # 打印周围代码
            print(content[idx-200:idx+200])

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done')
