'use strict';
const fs = require('fs');
const path = require('path');
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
const outputs = rows.map(({ problem_id, arguments: args }) => {
    const before = JSON.stringify(args);
    const result = require(path.join(__dirname, '..', 'javascript', `${problem_id}.js`)).solve(...args);
    if (JSON.stringify(args) !== before) throw new Error(`Input mutation: ${problem_id}`);
    return result;
});
process.stdout.write(JSON.stringify(outputs));
