"use strict";
// Hack2Hire 67f9969355e478de52401ddd (Top Love Message Receivers) over an INFERRED spec; qualification unknown.

// Binary min-heap over values compared by `less` (hole-based sifting).
class Heap {
  constructor(less, items) { this.less = less; this.a = items || []; for (let i = (this.a.length >> 1) - 1; i >= 0; i--) this.down(i); }
  get size() { return this.a.length; }
  push(x) {
    const a = this.a, less = this.less;
    let i = a.length;
    a.push(x);
    while (i > 0) { const p = (i - 1) >> 1, parent = a[p]; if (!less(x, parent)) break; a[i] = parent; i = p; }
    a[i] = x;
  }
  pop() { const a = this.a, top = a[0], last = a.pop(); if (a.length) { a[0] = last; this.down(0); } return top; }
  down(i) {
    const a = this.a, n = a.length, less = this.less, x = a[i];
    for (;;) {
      const l = 2 * i + 1;
      if (l >= n) break;
      let m = l;
      if (l + 1 < n && less(a[l + 1], a[l])) m = l + 1;
      if (!less(a[m], x)) break;
      a[i] = a[m];
      i = m;
    }
    a[i] = x;
  }
}

function solve(messages, k) {
  const pairs = new Set(), count = new Map();
  for (const [sender, receiver] of messages) {
    const key = sender + '\u0000' + receiver;
    if (!pairs.has(key)) { pairs.add(key); count.set(receiver, (count.get(receiver) || 0) + 1); }
  }
  const heap = new Heap((x, y) => x[0] > y[0] || (x[0] === y[0] && x[1] < y[1]), [...count].map(([name, c]) => [c, name]));
  const out = [];
  while (out.length < k && heap.size) out.push(heap.pop()[1]);
  return out;
}

function topReceivers(messages, k) { return solve(messages, k); }

module.exports = solve;
module.exports.topReceivers = topReceivers;
