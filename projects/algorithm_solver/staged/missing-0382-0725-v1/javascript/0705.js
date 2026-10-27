'use strict';

// 705. Design HashSet.

class MyHashSet {
  constructor() { this.bits = new Uint8Array(Math.ceil(1000001 / 8)); }
  add(key) { this.bits[key >> 3] |= 1 << (key & 7); }
  remove(key) { this.bits[key >> 3] &= 255 ^ (1 << (key & 7)); }
  contains(key) { return (this.bits[key >> 3] & (1 << (key & 7))) !== 0; }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MyHashSet(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MyHashSet;

if (typeof module !== 'undefined') module.exports = { solve, MyHashSet, Solution };
