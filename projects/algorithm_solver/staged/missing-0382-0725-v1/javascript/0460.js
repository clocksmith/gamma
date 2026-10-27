'use strict';

// 460. LFU Cache.

class LFUCache {
  constructor(capacity) {
    this.capacity = capacity; this.values = new Map(); this.frequencies = new Map();
    this.buckets = new Map(); this.minimum = 0;
  }
  _touch(key) {
    const frequency = this.frequencies.get(key);
    const bucket = this.buckets.get(frequency);
    bucket.delete(key);
    if (bucket.size === 0) {
      this.buckets.delete(frequency);
      if (this.minimum === frequency) this.minimum += 1;
    }
    this.frequencies.set(key, frequency + 1);
    if (!this.buckets.has(frequency + 1)) this.buckets.set(frequency + 1, new Set());
    this.buckets.get(frequency + 1).add(key);
  }
  get(key) {
    if (!this.values.has(key)) return -1;
    this._touch(key);
    return this.values.get(key);
  }
  put(key, value) {
    if (this.capacity === 0) return;
    if (this.values.has(key)) { this.values.set(key, value); this._touch(key); return; }
    if (this.values.size === this.capacity) {
      const bucket = this.buckets.get(this.minimum);
      const removed = bucket.values().next().value;
      bucket.delete(removed);
      if (bucket.size === 0) this.buckets.delete(this.minimum);
      this.values.delete(removed); this.frequencies.delete(removed);
    }
    this.values.set(key, value); this.frequencies.set(key, 1); this.minimum = 1;
    if (!this.buckets.has(1)) this.buckets.set(1, new Set());
    this.buckets.get(1).add(key);
  }
}


function solve(operations, args) {
  // Replay the native LeetCode interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new LFUCache(...args[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...args[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = LFUCache;
if (typeof module !== 'undefined') module.exports = { solve, Solution, LFUCache };
