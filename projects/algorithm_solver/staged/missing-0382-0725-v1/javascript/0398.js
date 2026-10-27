'use strict';

// 398. Random Pick Index.

class Solution {
  constructor(nums) {
    this.indices = new Map();
    nums.forEach((value, index) => {
      if (!this.indices.has(value)) this.indices.set(value, []);
      this.indices.get(value).push(index);
    });
  }
  pick(target) {
    const indices = this.indices.get(target);
    return indices[Math.floor(Math.random() * indices.length)];
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
