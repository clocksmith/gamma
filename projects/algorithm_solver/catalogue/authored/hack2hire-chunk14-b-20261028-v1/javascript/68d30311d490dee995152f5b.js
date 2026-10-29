"use strict";
// Hack2Hire 68d30311d490dee995152f5b (Weighted Cache) over an INFERRED spec; qualification unknown.

class Heap {
  constructor(less) { this.items = []; this.less = less; }
  get size() { return this.items.length; }
  push(x) {
    const a = this.items; a.push(x);
    let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (!this.less(a[i], a[p])) break; [a[i], a[p]] = [a[p], a[i]]; i = p; }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < a.length && this.less(a[l], a[m])) m = l;
        if (r < a.length && this.less(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]]; i = m;
      }
    }
    return top;
  }
}

class WeightedCache {
  constructor(maxTotalWeight) {
    this.limit = maxTotalWeight;
    this.items = new Map();
    this.heap = new Heap((x, y) => x[0] > y[0] || (x[0] === y[0] && x[1] < y[1]));
    this.total = 0;
    this.clock = 0;
  }

  put(key, value, weight) {
    this.clock++;
    const old = this.items.get(key);
    if (old !== undefined) this.total -= old[1];
    this.items.set(key, [value, weight, this.clock]);
    this.total += weight;
    this.heap.push([weight, this.clock, key]);
    while (this.total > this.limit) {
      const [w, stamp, victim] = this.heap.pop();
      const item = this.items.get(victim);
      if (item !== undefined && item[2] === stamp) { this.items.delete(victim); this.total -= w; }
    }
  }

  get(key) {
    const item = this.items.get(key);
    return item === undefined ? -1 : item[0];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WeightedCache" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new WeightedCache(...argumentLists[0]);
  const allowed = new Set(["put", "get"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.WeightedCache = WeightedCache;
