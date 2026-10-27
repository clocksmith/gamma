'use strict';
// 170. Two Sum III - Data structure design.
class TwoSum {
  constructor() { this.counts = new Map(); }
  add(number) { this.counts.set(number, (this.counts.get(number) || 0) + 1); }
  find(value) {
    for (const [number, count] of this.counts) {
      const other = value - number;
      if (this.counts.has(other) && (other !== number || count > 1)) return true;
    }
    return false;
  }
}
function solve(operations, args) {
  const structure = new TwoSum();
  return operations.map((operation, index) => operation === 'TwoSum' ? null : structure[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, TwoSum };
