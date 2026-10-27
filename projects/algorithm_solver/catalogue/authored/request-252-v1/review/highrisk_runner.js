"use strict";
// Candidate subprocess: receives inputs, never expected values.
const fs = require("fs");
const root = process.argv[2];
const requests = JSON.parse(fs.readFileSync(0, "utf8"));
const modules = new Map();
const outputs = requests.map(({pid, args}) => {
    if (!modules.has(pid)) modules.set(pid, require(`${root}/javascript/${pid}.js`));
    const original = JSON.stringify(args);
    const value = modules.get(pid).solve(...args);
    return {value, mutated: original !== JSON.stringify(args)};
});
process.stdout.write(JSON.stringify(outputs));
