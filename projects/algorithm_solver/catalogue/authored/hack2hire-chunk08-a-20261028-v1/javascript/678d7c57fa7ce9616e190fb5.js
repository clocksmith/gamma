"use strict";
// Hack2Hire 678d7c57fa7ce9616e190fb5 (Range Iterator) over an INFERRED spec; qualification unknown.

class RangeIterator {
  constructor(start, end, step) { this.current = start; this.end = end; this.step = step; }

  hasNext() { return this.step > 0 ? this.current < this.end : this.current > this.end; }

  next() {
    const value = this.current;
    this.current += this.step;
    return value;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RangeIterator" || argumentLists[0].length !== 3) throw new Error("exact initial constructor required");
  const instance = new RangeIterator(...argumentLists[0]);
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
module.exports.RangeIterator = RangeIterator;
