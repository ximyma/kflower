const fs = require('fs');
const content = fs.readFileSync('D:/kflower/kflower-frontend/src/common/pc/views/Templates.vue', 'utf8');
const scriptMatch = content.match(/<script[^>]*lang="ts"[^>]*>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.log('No script found'); process.exit(1); }
const script = scriptMatch[1];
const lines = script.split('\n');
console.log('Script total lines:', lines.length);

// Check for common issues
let openBraces = 0;
let issues = [];
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  // Count braces (rough)
  for (const ch of line) {
    if (ch === '{') openBraces++;
    if (ch === '}') openBraces--;
  }
  // Check for duplicate function declarations
  if (line.match(/function\s+importFromJson/)) {
    issues.push(`Line ${i+1}: importFromJson declaration: ${line.trim()}`);
  }
  if (line.match(/function\s+generateWithAI/)) {
    issues.push(`Line ${i+1}: generateWithAI declaration: ${line.trim()}`);
  }
  if (line.match(/function\s+publishTemplate/)) {
    issues.push(`Line ${i+1}: publishTemplate declaration: ${line.trim()}`);
  }
}

console.log('Final brace count:', openBraces, openBraces === 0 ? '(balanced)' : '(UNBALANCED!)');
console.log('\nFunction declarations found:');
issues.forEach(i => console.log(i));

// Check for 'return' outside function - find unmatched braces in function scope
let funcDepth = 0;
let inFunction = false;
let returnOutsideFunc = [];
for (let i = 0; i < lines.length; i++) {
  const line = lines[i].trim();
  if (line.match(/^(async\s+)?function\s+/) || line.match(/^(const|let|var)\s+\w+\s*=\s*(async\s*)?\(/)) {
    funcDepth++;
    inFunction = true;
  }
  for (const ch of lines[i]) {
    if (ch === '{') { /* already counted above */ }
    if (ch === '}') { 
      if (funcDepth > 0) funcDepth--;
    }
  }
  if (line.match(/^return\b/) && funcDepth === 0) {
    returnOutsideFunc.push(i + 1);
  }
}
if (returnOutsideFunc.length > 0) {
  console.log('\n"return" outside function at lines:', returnOutsideFunc.join(', '));
  returnOutsideFunc.forEach(ln => {
    console.log(`  ${ln}: ${lines[ln-1].trim()}`);
  });
}

// Also look for async async
for (let i = 0; i < lines.length; i++) {
  if (lines[i].match(/async\s+async\s+/)) {
    console.log(`\nDouble async at line ${i+1}: ${lines[i].trim()}`);
  }
  if (lines[i].match(/const\s+\w+\s*=\s*\w+\s*;\s*const\s+\1/)) {
    console.log(`\nPossible duplicate variable at line ${i+1}: ${lines[i].trim()}`);
  }
}

// Look for duplicate variable declarations
const varDecls = {};
for (let i = 0; i < lines.length; i++) {
  const match = lines[i].match(/(?:const|let|var)\s+(\w+)/);
  if (match) {
    const name = match[1];
    if (!varDecls[name]) varDecls[name] = [];
    varDecls[name].push(i + 1);
  }
}
console.log('\nDuplicate variable declarations:');
for (const [name, lineNums] of Object.entries(varDecls)) {
  if (lineNums.length > 1 && name.length > 2) {
    console.log(`  ${name}: lines ${lineNums.join(', ')}`);
  }
}
