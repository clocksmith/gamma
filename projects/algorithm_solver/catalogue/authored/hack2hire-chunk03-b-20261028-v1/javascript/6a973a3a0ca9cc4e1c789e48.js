"use strict";
// Hack2Hire 6a973a3a0ca9cc4e1c789e48 (Product of Maximum and Minimum) over an INFERRED spec; qualification unknown.

// Binary min-heap over arbitrary items with a strict "less" comparator.
class Heap {
  constructor(less) { this.items = []; this.less = less; }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(item) {
    const a = this.items; a.push(item);
    let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (!this.less(a[i], a[p])) break; [a[i], a[p]] = [a[p], a[i]]; i = p; }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last; let i = 0;
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

function solve(operations, x) {
  const count = new Map(), low = new Heap((a, b) => a < b), high = new Heap((a, b) => a > b), result = [];
  for (let i = 0; i < operations.length; i++) {
    const v = x[i];
    if (operations[i] === 'push') { count.set(v, (count.get(v) || 0) + 1); low.push(v); high.push(v); }
    else count.set(v, count.get(v) - 1);
    while (!count.get(low.peek())) low.pop();
    while (!count.get(high.peek())) high.pop();
    const product = low.peek() * high.peek();
    result.push(product === 0 ? 0 : product);  // normalise -0 to 0
  }
  return result;
}

function maxMinProducts(operations, x) { return solve(operations, x); }

module.exports = solve;
module.exports.maxMinProducts = maxMinProducts;
