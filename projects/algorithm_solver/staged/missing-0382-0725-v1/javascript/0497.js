'use strict';

// 497. Random Point in Non-overlapping Rectangles.

function _randomBelow(limit) {
  const bits = limit.toString(2).length;
  const mask = (1n << BigInt(bits)) - 1n;
  while (true) {
    let value = 0n;
    for (let generated = 0; generated < bits; generated += 26) {
      value = (value << 26n) | BigInt(Math.floor(Math.random() * 67108864));
    }
    value &= mask;
    if (value < limit) return value;
  }
}

class Solution {
  constructor(rects) {
    this.rects = rects.map(rectangle => rectangle.slice());
    this.prefix = [];
    let total = 0n;
    for (const [x1, y1, x2, y2] of this.rects) {
      total += (BigInt(x2) - BigInt(x1) + 1n) * (BigInt(y2) - BigInt(y1) + 1n);
      this.prefix.push(total);
    }
  }
  pick() {
    const ticket = _randomBelow(this.prefix[this.prefix.length - 1]);
    let left = 0, right = this.prefix.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (this.prefix[middle] <= ticket) left = middle + 1; else right = middle;
    }
    const offset = ticket - (left > 0 ? this.prefix[left - 1] : 0n);
    const [x1, y1, x2] = this.rects[left], width = BigInt(x2) - BigInt(x1) + 1n;
    return [x1 + Number(offset % width), y1 + Number(offset / width)];
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Solution(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

if (typeof module !== 'undefined') module.exports = { solve, Solution };
