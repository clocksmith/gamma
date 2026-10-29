"use strict";
// Hack2Hire 677bf4df5cbaff553b53b068 (Subarray-First Iterator) over an INFERRED spec; qualification unknown.

class SubarrayFirstIterator {
  constructor(a, b) { this.a = a; this.b = b; this.excluded = new Set(b); this.i = 0; this.j = 0; }

  hasNext() {
    if (this.i < this.b.length) return true;
    const a = this.a, excluded = this.excluded;
    while (this.j < a.length && excluded.has(a[this.j])) this.j++;
    return this.j < a.length;
  }

  next() {
    if (this.i < this.b.length) return this.b[this.i++];
    this.hasNext();
    return this.a[this.j++];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SubarrayFirstIterator" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new SubarrayFirstIterator(...argumentLists[0]);
  const allowed = new Set(["hasNext", "next"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SubarrayFirstIterator = SubarrayFirstIterator;
