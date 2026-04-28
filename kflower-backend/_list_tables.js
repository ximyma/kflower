const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('E:/kkflower/kflower-backend/kflower.db');

db.all("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name", [], (err, rows) => {
    if (err) { console.error(err); return; }
    console.log('=== Kflower 数据表 ===');
    rows.forEach(r => console.log('  ' + r.name));
    
    // 统计表数量
    console.log(`\n共 ${rows.length} 个表`);
    
    db.close();
});
