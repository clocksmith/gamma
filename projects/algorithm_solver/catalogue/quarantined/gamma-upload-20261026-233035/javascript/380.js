'use strict';
// 380. Insert Delete GetRandom O(1).
class RandomizedSet {
  constructor() { this.values = []; this.indices = new Map(); }
  insert(val) {
    if (this.indices.has(val)) return false;
    this.indices.set(val, this.values.length); this.values.push(val); return true;
  }
  remove(val) {
    if (!this.indices.has(val)) return false;
    const index = this.indices.get(val); this.indices.delete(val);
    const last = this.values.pop();
    if (index < this.values.length) { this.values[index] = last; this.indices.set(last, index); }
    return true;
  }
  getRandom() { return this.values[Math.floor(Math.random() * this.values.length)]; }
}
function solve(operations, args) {
  const structure = new RandomizedSet();
  return operations.map((operation, index) => operation === 'RandomizedSet' ? null : structure[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, RandomizedSet };
