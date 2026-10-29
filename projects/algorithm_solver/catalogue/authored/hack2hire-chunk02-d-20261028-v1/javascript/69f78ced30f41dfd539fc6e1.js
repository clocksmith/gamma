"use strict";
// Hack2Hire 69f78ced30f41dfd539fc6e1 (Design a Spreadsheet with Formula Evaluation, level 2) over an INFERRED spec; qualification unknown.

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

  reaches(sources, goal) {
    const seen = new Set();
    const stack = sources.slice();
    while (stack.length) {
      const name = stack.pop();
      if (name === goal) return true;
      if (seen.has(name)) continue;
      seen.add(name);
      for (const t of this.cells.get(name) || []) if (typeof t === "string") stack.push(t);
    }
    return false;
  }

  setCell(cell, value) {
    const terms = parseContent(value);
    if (this.reaches(terms.filter((t) => typeof t === "string"), cell)) return false;
    this.cells.set(cell, terms);
    return true;
  }
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
