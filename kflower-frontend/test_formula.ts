// 测试前端公式引擎
// 运行：cd kflower-frontend && npx tsx test_formula.ts

function evaluateFormula(formula: string, ctx: Record<string, any>): any {
  if (!formula) return undefined
  try {
    // 替换 {字段名} 为实际值
    let expr = formula.replace(/\{([^}]+)\}/g, (_match: string, fieldName: string) => {
      const val = ctx[fieldName.trim()]
      if (val === undefined || val === null || val === '') return '0'
      const num = Number(val)
      return isNaN(num) ? JSON.stringify(String(val)) : String(num)
    })

    // 支持函数
    expr = expr
      .replace(/\bROUND\b/g, 'Math.round')
      .replace(/\bFLOOR\b/g, 'Math.floor')
      .replace(/\bCEIL\b/g, 'Math.ceil')
      .replace(/\bABS\b/g, 'Math.abs')
      .replace(/\bSQRT\b/g, 'Math.sqrt')
      .replace(/\bPOWER\b/g, 'Math.pow')
      .replace(/\bMAX\b/g, 'Math.max')
      .replace(/\bMIN\b/g, 'Math.min')

    // 使用 Function 沙箱
    const fn = new Function('Math', `"use strict"; return (${expr})`)
    const result = fn(Math)
    if (typeof result === 'number' && !isNaN(result)) {
      return Math.round(result * 1e10) / 1e10
    }
    return result
  } catch (e) {
    console.error('Formula error:', e)
    return undefined
  }
}

console.log('=== Frontend Formula Engine Tests ===')

// 1. 基础计算
const r1 = evaluateFormula('{单价} * {数量}', {单价：100, 数量：5})
console.log(`1. Basic: ${r1} (expected: 500)`)
console.assert(r1 === 500, `Expected 500, got ${r1}`)

// 2. ROUND
const r2 = evaluateFormula('ROUND({price} * 0.13, 2)', {price: 100})
console.log(`2. ROUND: ${r2} (expected: 13)`)
console.assert(r2 === 13, `Expected 13, got ${r2}`)

// 3. CONCAT
const r3 = evaluateFormula('CONCAT({first}, "-", {last})', {first: 'John', last: 'Doe'})
console.log(`3. CONCAT: ${r3} (expected: John-Doe)`)
console.assert(r3 === 'John-Doe', `Expected John-Doe, got ${r3}`)

console.log('All frontend tests passed!')
