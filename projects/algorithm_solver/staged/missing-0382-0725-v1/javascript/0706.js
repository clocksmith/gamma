'use strict';

// 706. Design HashMap.

class MyHashMap {
  constructor() { this.buckets = Array.from({length: 1009}, () => []); }
  put(key, value) {
    const bucket = this.buckets[key % this.buckets.length];
    for (const entry of bucket) if (entry[0] === key) { entry[1] = value; return; }
    bucket.push([key, value]);
  }
  get(key) {
    for (const [stored, value] of this.buckets[key % this.buckets.length]) if (stored === key) return value;
    return -1;
  }
  remove(key) {
    const bucket = this.buckets[key % this.buckets.length];
    for (let i = 0; i < bucket.length; i += 1) if (bucket[i][0] === key) {
      bucket[i] = bucket[bucket.length - 1]; bucket.pop(); return;
    }
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MyHashMap(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MyHashMap;

if (typeof module !== 'undefined') module.exports = { solve, MyHashMap, Solution };
