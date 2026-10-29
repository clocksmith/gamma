"use strict";
// Hack2Hire 68d84fa6ae12841706c1fc81 (MinMax Queue) over an INFERRED spec; qualification unknown.

class MinMaxQueue {
  constructor() {
    this.items = []; this.head = 0;
    this.lows = []; this.lowHead = 0; // non-decreasing candidates for the minimum
    this.highs = []; this.highHead = 0; // non-increasing candidates for the maximum
  }

  enqueue(val) {
    this.items.push(val);
    while (this.lows.length > this.lowHead && this.lows[this.lows.length - 1] > val) this.lows.pop();
    this.lows.push(val);
    while (this.highs.length > this.highHead && this.highs[this.highs.length - 1] < val) this.highs.pop();
    this.highs.push(val);
  }

  dequeue() {
    const val = this.items[this.head++];
    if (this.lows[this.lowHead] === val) this.lowHead++;
    if (this.highs[this.highHead] === val) this.highHead++;
    return val;
  }

  getMin() { return this.lows[this.lowHead]; }

  getMax() { return this.highs[this.highHead]; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MinMaxQueue" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new MinMaxQueue(...argumentLists[0]);
  const allowed = new Set(["enqueue", "dequeue", "getMin", "getMax"]);
  const voids = new Set(["enqueue"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(voids.has(operationNames[i]) ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.MinMaxQueue = MinMaxQueue;
