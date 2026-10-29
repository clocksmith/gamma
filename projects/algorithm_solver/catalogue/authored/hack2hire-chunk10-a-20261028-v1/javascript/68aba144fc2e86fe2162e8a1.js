"use strict";
// Hack2Hire 68aba144fc2e86fe2162e8a1 (Design Cache with Eviction, variant 2 of 2) over an INFERRED spec; qualification unknown.

class MinHeap {
  // entries are arrays compared element-wise on their first two (numeric) fields
  constructor() { this.items = []; }
  get size() { return this.items.length; }
  static less(a, b) { return a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]); }
  push(x) {
    const h = this.items; h.push(x);
    let i = h.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (!MinHeap.less(h[i], h[p])) break; [h[i], h[p]] = [h[p], h[i]]; i = p; }
  }
  peek() { return this.items[0]; }
  pop() {
    const h = this.items, top = h[0], last = h.pop();
    if (h.length) {
      h[0] = last; let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < h.length && MinHeap.less(h[l], h[m])) m = l;
        if (r < h.length && MinHeap.less(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]]; i = m;
      }
    }
    return top;
  }
}

class RankedCache {
  constructor(capacity, source) {
    this.capacity = capacity;
    this.entries = new Map(); // key -> [value, rank, write sequence]
    this.heap = new MinHeap(); // [rank, write sequence, key]; stale when the sequence no longer matches
    this.seq = 0;
    this.source = new Map(source.map((row) => [row[0], [row[1], row[2]]])); // private copy of the data source
    this.loads = 0;
  }

  _write(key, value, rank) {
    this.seq += 1;
    if (!this.entries.has(key) && this.entries.size === this.capacity) {
      for (;;) {
        const [, seq, victim] = this.heap.pop();
        const entry = this.entries.get(victim);
        if (entry !== undefined && entry[2] === seq) { this.entries.delete(victim); break; }
      }
    }
    this.entries.set(key, [value, rank, this.seq]);
    this.heap.push([rank, this.seq, key]);
  }

  put(key, value, rank) {
    this._write(key, value, rank);
    this.source.set(key, [value, rank]); // write-through
  }

  get(key) {
    const entry = this.entries.get(key);
    if (entry !== undefined) return entry[0];
    const stored = this.source.get(key);
    if (stored !== undefined) { this.loads += 1; this._write(key, stored[0], stored[1]); return stored[0]; }
    return "";
  }

  getLoadCount() { return this.loads; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RankedCache" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new RankedCache(...argumentLists[0]);
  const allowed = new Set(["put", "get", "getLoadCount"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RankedCache = RankedCache;
