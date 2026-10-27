'use strict';

// 528. Random Pick with Weight.

class Solution {
  constructor(w) {
    this.prefix = [];
    let total = 0;
    for (const weight of w) { total += weight; this.prefix.push(total); }
  }
  pickIndex() {
    const ticket = Math.floor(Math.random() * this.prefix[this.prefix.length - 1]);
    let left = 0, right = this.prefix.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (this.prefix[middle] <= ticket) left = middle + 1; else right = middle;
    }
    return left;
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
