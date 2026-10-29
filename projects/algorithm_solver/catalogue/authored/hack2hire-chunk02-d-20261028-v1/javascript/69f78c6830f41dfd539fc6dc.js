"use strict";
// Hack2Hire 69f78c6830f41dfd539fc6dc (Design a Spreadsheet with Formula Evaluation, level 1) over an INFERRED spec; qualification unknown.

function parseContent(value) {
  if (value[0] !== "=") return [Number(value)];
  return value.slice(1).split("+").map((term) => (term[0] >= "A" && term[0] <= "Z" ? term : Number(term)));
}

class Spreadsheet {
  constructor() { this.cells = new Map(); }

  resetCell(cell) { this.cells.delete(cell); }

  getCell(cell) {
    const memo = new Map();
    const stack = [cell];
    while (stack.length) {
      const name = stack[stack.length - 1];
      if (memo.has(name)) { stack.pop(); continue; }
      const terms = this.cells.get(name) || [];
      let waiting = false;
      for (const t of terms) if (typeof t === "string" && !memo.has(t)) { stack.push(t); waiting = true; }
      if (waiting) continue;
      stack.pop();
      let total = 0;
      for (const t of terms) total += typeof t === "string" ? memo.get(t) : t;
      memo.set(name, total);
    }
    return memo.get(cell);
  }

  setCell(cell, value) { this.cells.set(cell, parseContent(value)); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Spreadsheet" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new Spreadsheet(...argumentLists[0]);
  const allowed = new Set(["setCell", "getCell", "resetCell"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Spreadsheet = Spreadsheet;
