"use strict";
// Hack2Hire 67843d1e0e1dbb6a0938577d (Find Eligible Order Sequence) over an INFERRED spec; qualification unknown.

class MinHeap {
  constructor(less) { this.items = []; this.less = less; }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(x) {
    const h = this.items; h.push(x);
    let i = h.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!this.less(h[i], h[p])) break;
      [h[i], h[p]] = [h[p], h[i]]; i = p;
    }
  }
  pop() {
    const h = this.items, top = h[0], last = h.pop();
    if (h.length) {
      h[0] = last; let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < h.length && this.less(h[l], h[m])) m = l;
        if (r < h.length && this.less(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]]; i = m;
      }
    }
    return top;
  }
}

function solve(orderIds) {
  const a = orderIds, n = a.length;
  const prev = Array.from({length: n}, (_, i) => i - 1), next = Array.from({length: n}, (_, i) => i + 1);
  const queued = new Uint8Array(n);
  const eligible = (i) => (prev[i] < 0 || a[i] > a[prev[i]]) && (next[i] >= n || a[i] > a[next[i]]);
  const heap = new MinHeap((x, y) => x[0] < y[0]);
  for (let i = 0; i < n; i++) if (eligible(i)) { queued[i] = 1; heap.push([a[i], i]); }
  const out = [];
  while (heap.size) {
    const [v, i] = heap.pop();
    out.push(v);
    const p = prev[i], q = next[i];
    if (p >= 0) next[p] = q;
    if (q < n) prev[q] = p;
    for (const j of [p, q]) {
      if (j >= 0 && j < n && !queued[j] && eligible(j)) { queued[j] = 1; heap.push([a[j], j]); }
    }
  }
  return out;
}

function eligibleOrderSequence(orderIds) { return solve(orderIds); }

module.exports = solve;
module.exports.eligibleOrderSequence = eligibleOrderSequence;
