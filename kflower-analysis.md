# 矩阵模板字段不显示问题分析报告

## 问题回顾
用户报告：矩阵模板创建后，进入 FormListPage.vue 时字段名称不显示。

## 代码追踪结论

### 1. 数据流验证
- ✅ 数据库 `modules` 字段正常存储了 `label` 属性（已验证模板29）
- ✅ `TemplateResponse` Schema 中 `modules: List[Dict]` 正确传递字段
- ✅ `FormListPage.loadTemplate()` 从 `mod.fields` 正确提取 `name/label/type`
- ✅ `displayFields` 和 `formFields` 都正确赋值

### 2. 关键发现：后端 `saveTemplate` 和 `confirmCreateMatrixTemplate` 均正确设置 `label`

**普通模板创建** (`saveTemplate`)：
```javascript
modules:[{ name:'main', label:'主表单', fields: fieldsToSave }]
```

**矩阵模板创建** (`confirmCreateMatrixTemplate`)：
```javascript
fields = [
  { name: 'row_dimension', label: rowDimLabel, ... },
  { name: 'col_dimension', label: colDimLabel, ... },
  { name: 'value', label: valueLabel, ... }
]
modules: [{ name: 'main', label: '矩阵数据录入', fields }]
```

两者都正确传递了 `label`。

### 3. 已排除的问题
- ❌ 不是 `modules` 结构问题 — 模块名固定为 `'main'`，但代码从 `mod.fields` 提取，不依赖模块名
- ❌ 不是后端 `TemplateResponse` 丢失字段 — Schema 中 `modules: List[Dict]` 完整传递
- ❌ 不是 `displayFields` 提取逻辑错误 — `label` 明确从 `f.label` 提取

### 4. 下一步建议
由于直接代码逻辑未发现明显 Bug，建议：

1. **重启后端服务** — 当前后端端口 `8879` 无监听，可能服务未启动
2. **检查浏览器 Network 面板** — 看 `/api/v1/templates/{id}` 返回的 `modules` 中是否真的包含 `label` 字段
3. **检查 F12 Console** — 看 `loadTemplate` 中 `console.log` 输出是否包含 `label`
4. **确认实际端口** — vite proxy 代理到哪个端口需要检查 `vite.config.ts`

## 临时诊断方案
在 `FormListPage.vue` 的 `loadTemplate` 中加一行 `console.log`：
```javascript
console.log('[loadTemplate] 加载的 modules:', JSON.stringify(res.modules))
```
刷新页面后查看控制台输出，确认后端返回的字段中是否有 `label`。

---

_分析时间：2026-05-04_
