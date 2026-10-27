'use strict';

// 519. Random Flip Matrix.

class Solution {
  constructor(m, n) { this.rows = m; this.cols = n; this.remaining = m * n; this.mapping = new Map(); }
  flip() {
    const ticket = Math.floor(Math.random() * this.remaining);
    this.remaining -= 1;
    const cell = this.mapping.has(ticket) ? this.mapping.get(ticket) : ticket;
    const replacement = this.mapping.has(this.remaining) ? this.mapping.get(this.remaining) : this.remaining;
    this.mapping.set(ticket, replacement); this.mapping.delete(this.remaining);
    return [Math.floor(cell / this.cols), cell % this.cols];
  }
  reset() { this.remaining = this.rows * this.cols; this.mapping.clear(); }
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
