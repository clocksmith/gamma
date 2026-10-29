"use strict";
// Hack2Hire 67e8af3a7131f7c901ffd7a1 (Find Maximum Trade Shares). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(item) {
    const a = this.items;
    a.push(item);
    let i = a.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!this.less(a[i], a[p])) break;
      [a[i], a[p]] = [a[p], a[i]];
      i = p;
    }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < a.length && this.less(a[l], a[m])) m = l;
        if (r < a.length && this.less(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]];
        i = m;
      }
    }
    return top;
  }
}

function solve(orders) {
  const byKey = (x, y) => x[0] < y[0];
  const sells = new MinHeap(byKey), buys = new MinHeap(byKey), remaining = [];
  let traded = 0;
  for (const [price, quantity, kind] of orders) {
    let left = quantity;
    const isBuy = kind === "buy";
    const book = isBuy ? sells : buys, own = isBuy ? buys : sells;
    while (left > 0 && book.size > 0 && (isBuy ? book.peek()[0] <= price : -book.peek()[0] >= price)) {
      const index = book.peek()[1], take = Math.min(left, remaining[index]);
      traded += take;
      left -= take;
      remaining[index] -= take;
      if (remaining[index] === 0) book.pop();
    }
    if (left > 0) {
      remaining.push(left);
      own.push([isBuy ? -price : price, remaining.length - 1]);
    }
  }
  return traded;
}

function maxTradedShares(orders) { return solve(orders); }
module.exports = solve;
module.exports.maxTradedShares = maxTradedShares;
