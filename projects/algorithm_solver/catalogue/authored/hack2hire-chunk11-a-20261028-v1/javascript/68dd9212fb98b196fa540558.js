"use strict";
// Hack2Hire 68dd9212fb98b196fa540558 (Flatten 2D Array With Remove) over an INFERRED spec; qualification unknown.

class Vector2D {
  constructor(vec) {
    this.rows = vec.map((row) => row.slice());
    this.dead = vec.map((row) => new Array(row.length).fill(false)); // lazy removal flags
    this.removed = new Array(vec.length).fill(0);
    this.r = 0; this.c = 0; this.last = null;
  }

  skip() {
    const rows = this.rows;
    while (this.r < rows.length && this.c >= rows[this.r].length) { this.r++; this.c = 0; }
  }

  next() {
    this.skip();
    const value = this.rows[this.r][this.c];
    this.last = [this.r, this.c];
    this.c++;
    return value;
  }

  hasNext() {
    this.skip();
    return this.r < this.rows.length;
  }

  remove() {
    if (this.last === null) return false;
    const [r, c] = this.last;
    this.dead[r][c] = true;
    this.removed[r]++;
    this.last = null;
    return true;
  }

  getVector() {
    return this.rows.map((row, r) => (this.removed[r] === 0 ? row.slice() : row.filter((_, c) => !this.dead[r][c])));
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Vector2D" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new Vector2D(...argumentLists[0]);
  const allowed = new Set(["next", "hasNext", "remove", "getVector"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Vector2D = Vector2D;
