"use strict";
// Hack2Hire 688102fcf96758aa78e1d67a (Find Minimal Shoppers). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

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

function solve(orders, maxAverageWait) {
  const n = orders.length;
  const sequence = orders.map((_, i) => i).sort((i, j) => orders[i][1] - orders[j][1] || i - j);
  const totalWait = (shoppers) => {
    const free = new MinHeap((x, y) => x < y);
    for (let s = 0; s < shoppers; s++) free.push(0);
    let total = 0;
    for (const i of sequence) {
      const [duration, arrival] = orders[i];
      const finish = Math.max(free.pop(), arrival) + duration;
      free.push(finish);
      total += finish - arrival;
    }
    return total;
  };
  const limit = maxAverageWait * n;
  if (totalWait(n) > limit) return -1;
  let low = 1, high = n;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (totalWait(middle) <= limit) high = middle;
    else low = middle + 1;
  }
  return low;
}

function minShoppers(orders, maxAverageWait) { return solve(orders, maxAverageWait); }
module.exports = solve;
module.exports.minShoppers = minShoppers;
