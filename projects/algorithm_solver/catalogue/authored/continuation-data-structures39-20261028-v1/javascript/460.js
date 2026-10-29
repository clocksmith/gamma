"use strict";

class LFUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.minFreq = 0;
    this.keyValFreq = new Map();
    this.freqKeys = new Map();
  }
  _touch(key, newVal) {
    const entry = this.keyValFreq.get(key);
    const val = newVal !== undefined ? newVal : entry[0];
    const freq = entry[1];
    const bucket = this.freqKeys.get(freq);
    bucket.delete(key);
    if (bucket.size === 0) {
      this.freqKeys.delete(freq);
      if (this.minFreq === freq) this.minFreq += 1;
    }
    const nxtFreq = freq + 1;
    let nxtBucket = this.freqKeys.get(nxtFreq);
    if (!nxtBucket) {
      nxtBucket = new Set();
      this.freqKeys.set(nxtFreq, nxtBucket);
    }
    nxtBucket.add(key);
    this.keyValFreq.set(key, [val, nxtFreq]);
    return val;
  }
  get(key) {
    if (!this.keyValFreq.has(key)) return -1;
    return this._touch(key);
  }
  put(key, value) {
    if (this.cap <= 0) return;
    if (this.keyValFreq.has(key)) {
      this._touch(key, value);
      return;
    }
    if (this.keyValFreq.size === this.cap) {
      const minBucket = this.freqKeys.get(this.minFreq);
      const evictKey = minBucket.values().next().value;
      minBucket.delete(evictKey);
      if (minBucket.size === 0) this.freqKeys.delete(this.minFreq);
      this.keyValFreq.delete(evictKey);
    }
    this.keyValFreq.set(key, [value, 1]);
    let bucket1 = this.freqKeys.get(1);
    if (!bucket1) {
      bucket1 = new Set();
      this.freqKeys.set(1, bucket1);
    }
    bucket1.add(key);
    this.minFreq = 1;
  }
}

function solve(operation_names, argument_lists) {
  const instance = new LFUCache(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "get") out.push(instance.get(args[0]));
    else if (op === "put") { instance.put(args[0], args[1]); out.push(null); }
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.LFUCache = LFUCache;
