"use strict";
// Hack2Hire 68aceb961bf7d2097f647f62 (Product Price Tracker) over an INFERRED spec; qualification unknown.

// Binary heap over parallel arrays of (price, timestamp); sign = 1 for a min-heap, -1 for a max-heap.
class LazyHeap {
  constructor(sign) { this.sign = sign; this.key = []; this.stamp = []; }

  less(i, j) { return this.sign * this.key[i] < this.sign * this.key[j]; }

  swap(i, j) {
    const k = this.key[i]; this.key[i] = this.key[j]; this.key[j] = k;
    const s = this.stamp[i]; this.stamp[i] = this.stamp[j]; this.stamp[j] = s;
  }

  push(price, timestamp) {
    this.key.push(price); this.stamp.push(timestamp);
    let i = this.key.length - 1;
    while (i > 0) {
      const up = (i - 1) >> 1;
      if (!this.less(i, up)) break;
      this.swap(i, up); i = up;
    }
  }

  pop() {
    const end = this.key.length - 1;
    this.swap(0, end); this.key.pop(); this.stamp.pop();
    const n = this.key.length;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let top = i;
      if (l < n && this.less(l, top)) top = l;
      if (r < n && this.less(r, top)) top = r;
      if (top === i) break;
      this.swap(i, top); i = top;
    }
  }

  topValid(prices) {
    while (this.key.length && prices.get(this.stamp[0]) !== this.key[0]) this.pop();
    return this.key.length ? this.key[0] : -1;
  }
}

class ProductPrice {
  constructor() {
    this.prices = new Map();
    this.latest = 0;
    this.high = new LazyHeap(-1);
    this.low = new LazyHeap(1);
  }

  update(timestamp, price) {
    this.prices.set(timestamp, price);
    if (timestamp > this.latest) this.latest = timestamp;
    this.high.push(price, timestamp);
    this.low.push(price, timestamp);
  }

  current() {
    return this.prices.size ? this.prices.get(this.latest) : -1;
  }

  maximum() {
    return this.high.topValid(this.prices);
  }

  minimum() {
    return this.low.topValid(this.prices);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ProductPrice" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new ProductPrice(...argumentLists[0]);
  const allowed = new Set(["update", "current", "maximum", "minimum"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ProductPrice = ProductPrice;
