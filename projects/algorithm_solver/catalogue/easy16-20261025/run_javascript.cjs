"use strict";
// Inputs only. This is a development runner, not a security sandbox.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function containers(value, found = new Set()) {
  if (value !== null && typeof value === "object" && !found.has(value)) {
    found.add(value);
    for (const item of Object.values(value)) containers(item, found);
  }
  return found;
}

const functions = new Map();
const answers = JSON.parse(fs.readFileSync(0, "utf8")).map(row => {
  const id = String(row.id);
  if (!/^[0-9]+$/.test(id)) throw new Error("Expected a numeric problem ID");
  if (!functions.has(id)) {
    const source = fs.readFileSync(path.join(__dirname, "javascript", `${id}.js`), "utf8");
    functions.set(id, vm.runInNewContext(`${source}\nsolve;`, {}, {timeout: 1000}));
  }
  const before = JSON.stringify(row.args);
  const inputObjects = containers(row.args);
  const result = functions.get(id)(...row.args);
  return {
    result,
    unchanged: JSON.stringify(row.args) === before,
    aliases_input: [...containers(result)].some(value => inputObjects.has(value)),
  };
});
process.stdout.write(JSON.stringify(answers) + "\n");
