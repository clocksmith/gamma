"use strict";
// Hack2Hire 678d6982fa7ce9616e190fb3 (Interleave Iterator with Cycle) over an INFERRED spec; qualification unknown.

class InterleaveIterator {
  constructor(arrays, cycle) {
    this.arrays = arrays.filter((a) => a.length > 0).map((a) => a.slice());
    this.cycle = cycle;
    this.refill();
  }

  refill() {
    this.queueIndex = [];
    this.queuePosition = [];
    for (let i = 0; i < this.arrays.length; i++) { this.queueIndex.push(i); this.queuePosition.push(0); }
    this.head = 0;
  }

  hasNext() {
    return this.head < this.queueIndex.length || (this.cycle && this.arrays.length > 0);
  }

  next() {
    if (this.head >= this.queueIndex.length) {
      if (!(this.cycle && this.arrays.length > 0)) return null;
      this.refill();
    }
    const i = this.queueIndex[this.head], position = this.queuePosition[this.head];
    this.head++;
    const values = this.arrays[i];
    if (position + 1 < values.length) { this.queueIndex.push(i); this.queuePosition.push(position + 1); }
    if (this.head > 65536 && this.head * 2 > this.queueIndex.length) {
      this.queueIndex = this.queueIndex.slice(this.head);
      this.queuePosition = this.queuePosition.slice(this.head);
      this.head = 0;
    }
    return values[position];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InterleaveIterator" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new InterleaveIterator(...argumentLists[0]);
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
module.exports.InterleaveIterator = InterleaveIterator;
