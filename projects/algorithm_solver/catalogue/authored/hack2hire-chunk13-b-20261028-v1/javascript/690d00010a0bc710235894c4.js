"use strict";
// Hack2Hire 690d00010a0bc710235894c4 (Sparse Matrix Operation) over an INFERRED spec; qualification unknown.

const byNumber = (x, y) => x - y;

class SparseMatrix {
  constructor(matrix) {
    this.rows = matrix.length;
    this.cols = matrix[0].length;
    this.data = new Map(); // row -> Map(col -> non-zero value)
    matrix.forEach((row, i) => {
      const entries = new Map();
      row.forEach((v, j) => { if (v !== 0) entries.set(j, v); });
      if (entries.size) this.data.set(i, entries);
    });
  }

  get(row, col) {
    const entries = this.data.get(row);
    return entries !== undefined && entries.has(col) ? entries.get(col) : 0;
  }

  set(row, col, value) {
    if (value !== 0) {
      if (!this.data.has(row)) this.data.set(row, new Map());
      this.data.get(row).set(col, value);
    } else {
      const entries = this.data.get(row);
      if (entries !== undefined && entries.has(col)) {
        entries.delete(col);
        if (!entries.size) this.data.delete(row);
      }
    }
  }

  add(other) {
    const out = [];
    for (let i = 0; i < this.rows; i++) {
      const acc = new Map(this.data.get(i) || []);
      other[i].forEach((v, j) => { if (v !== 0) acc.set(j, (acc.get(j) || 0) + v); });
      for (const j of [...acc.keys()].sort(byNumber)) if (acc.get(j) !== 0) out.push([i, j, acc.get(j)]);
    }
    return out;
  }

  multiply(other) {
    const otherRows = other.map((row) => { const nz = []; row.forEach((v, j) => { if (v !== 0) nz.push([j, v]); }); return nz; });
    const out = [];
    for (const i of [...this.data.keys()].sort(byNumber)) {
      const acc = new Map();
      for (const [t, a] of this.data.get(i)) for (const [j, b] of otherRows[t]) acc.set(j, (acc.get(j) || 0) + a * b);
      for (const j of [...acc.keys()].sort(byNumber)) if (acc.get(j) !== 0) out.push([i, j, acc.get(j)]);
    }
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SparseMatrix" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new SparseMatrix(...argumentLists[0]);
  const allowed = new Set(["get", "set", "add", "multiply"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SparseMatrix = SparseMatrix;
