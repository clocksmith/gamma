"use strict";
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..', 'javascript');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = cases.map(row => {
    const before = JSON.stringify(row.args);
    const answer = require(path.join(root, row.id + '.js')).solve(...row.args);
    if (JSON.stringify(row.args) !== before) throw new Error('Unexpected mutation: '+row.id);
    return answer;
});
const {TaskManager} = require(path.join(root, '3408.js'));
const manager = new TaskManager([[9,1,7]]);
manager.edit(1,7); manager.rmv(1); manager.add(5,1,7);
if (manager.execTop() !== 5 || manager.execTop() !== -1) throw new Error('Native TaskManager failed');
process.stdout.write(JSON.stringify(results));
