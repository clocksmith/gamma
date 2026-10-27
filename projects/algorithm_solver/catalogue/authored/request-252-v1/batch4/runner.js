'use strict';
const fs = require('fs');
const path = require('path');
const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
const answers = requests.map(({ id, args }) => {
    const before = JSON.stringify(args);
    const { solve } = require(path.join(__dirname, '..', 'javascript', `${id}.js`));
    const result = solve(...args);
    return { result, unchanged: JSON.stringify(args) === before };
});
process.stdout.write(JSON.stringify(answers));
