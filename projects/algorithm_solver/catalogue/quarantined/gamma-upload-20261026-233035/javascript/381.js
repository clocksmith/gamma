'use strict';
// 381. Insert Delete GetRandom O(1) - Duplicates allowed.
class RandomizedCollection {
  constructor() { this.values = []; this.indices = new Map(); }
  insert(val) {
    if (!this.indices.has(val)) this.indices.set(val, new Set());
    const fresh = this.indices.get(val).size === 0;
    this.indices.get(val).add(this.values.length); this.values.push(val); return fresh;
  }
  remove(val) {
    if (!this.indices.has(val) || this.indices.get(val).size === 0) return false;
    const index = this.indices.get(val).values().next().value;
    this.indices.get(val).delete(index);
    const lastIndex = this.values.length - 1; const last = this.values[lastIndex];
    if (index !== lastIndex) {
      this.values[index] = last; this.indices.get(last).delete(lastIndex); this.indices.get(last).add(index);
    }
    this.values.pop(); return true;
  }
  getRandom() { return this.values[Math.floor(Math.random() * this.values.length)]; }
}
function solve(operations, args) {
  const structure = new RandomizedCollection();
  return operations.map((operation, index) => operation === 'RandomizedCollection' ? null : structure[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, RandomizedCollection };
