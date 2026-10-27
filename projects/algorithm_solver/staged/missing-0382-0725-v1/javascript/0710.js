'use strict';

// 710. Random Pick with Blacklist.

class BlacklistPicker {
  constructor(n, blacklist) {
    const blocked = new Set(blacklist);
    this.limit = n - blacklist.length; this.mapping = new Map();
    let replacement = this.limit;
    for (const value of blacklist) {
      if (value >= this.limit) continue;
      while (blocked.has(replacement)) replacement += 1;
      this.mapping.set(value, replacement++);
    }
  }
  pick() {
    const value = Math.floor(Math.random() * this.limit);
    return this.mapping.has(value) ? this.mapping.get(value) : value;
  }
}


function solve(operations, args) {
  // Replay the native LeetCode interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new BlacklistPicker(...args[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...args[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = BlacklistPicker;
if (typeof module !== 'undefined') module.exports = { solve, Solution, BlacklistPicker };
