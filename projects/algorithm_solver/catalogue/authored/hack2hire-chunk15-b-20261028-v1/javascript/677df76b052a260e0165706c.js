"use strict";
// Hack2Hire 677df76b052a260e0165706c (Design Infinite Queue with GetRandom O(1)) over an INFERRED spec; qualification unknown.

class InfiniteQueue {
  constructor() {
    this.items = [];
    this.head = 0;
  }

  add(value) {
    this.items.push(value);
  }

  poll() {
    if (this.head === this.items.length) return -1;
    const value = this.items[this.head];
    this.head++;
    if (this.head * 2 >= this.items.length && this.head >= 1024) {
      this.items = this.items.slice(this.head);
      this.head = 0;
    }
    return value;
  }

  getRandom(r) {
    const size = this.items.length - this.head;
    if (size === 0) return -1;
    return this.items[this.head + (r % size)];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InfiniteQueue" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new InfiniteQueue(...argumentLists[0]);
  const allowed = new Set(["add", "poll", "getRandom"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.InfiniteQueue = InfiniteQueue;
