"use strict";
// Hack2Hire 6913b4310ac116974ccedd13 (GPU Credits II); INFERRED spec; qualification unknown.
function cmpStr(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function before(a, b) { return a[0] !== b[0] ? a[0] < b[0] : a[1] !== b[1] ? a[1] < b[1] : a[2] < b[2]; } // (end, start, id)
function push(heap, item) {
  heap.push(item);
  for (let i = heap.length - 1; i > 0;) { const p = (i - 1) >> 1; if (!before(heap[i], heap[p])) break; [heap[i], heap[p]] = [heap[p], heap[i]]; i = p; }
}
function pop(heap) {
  const top = heap[0], last = heap.pop();
  if (heap.length) {
    heap[0] = last;
    for (let i = 0; ;) {
      const l = 2 * i + 1, r = l + 1; let m = i;
      if (l < heap.length && before(heap[l], heap[m])) m = l;
      if (r < heap.length && before(heap[r], heap[m])) m = r;
      if (m === i) break; [heap[i], heap[m]] = [heap[m], heap[i]]; i = m;
    }
  }
  return top;
}
class CreditSystem {
  constructor() { this.grants = []; this.consumes = []; }
  replay(until, stopArrival) {
    const grants = this.grants.filter(g => g[0] <= until).sort((a, b) => a[0] - b[0] || a[1] - b[1] || cmpStr(a[2], b[2]));
    const consumes = this.consumes.filter(c => c[0] <= until && (stopArrival === undefined || c[0] < until || c[1] <= stopArrival))
      .sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const heap = [], remaining = new Map();
    let total = 0, gi = 0, outcome = null;
    const advance = t => {
      while (gi < grants.length && grants[gi][0] <= t) {
        const [start, end, id, amount] = grants[gi++];
        remaining.set(id, amount); total += amount; push(heap, [end, start, id]);
      }
      while (heap.length && heap[0][0] < t) total -= remaining.get(pop(heap)[2]);
    };
    for (const [t, arrival, amount0] of consumes) {
      advance(t);
      let amount = amount0;
      const ok = total >= amount;
      if (ok) {
        total -= amount;
        while (amount > 0) {
          const id = heap[0][2], take = Math.min(amount, remaining.get(id));
          remaining.set(id, remaining.get(id) - take); amount -= take;
          if (remaining.get(id) === 0) pop(heap);
        }
      }
      if (arrival === stopArrival) outcome = ok;
    }
    advance(until);
    return [total, outcome];
  }
  addCredit(creditId, amount, startTime, endTime) { this.grants.push([startTime, endTime, creditId, amount]); }
  consumeCredit(amount, timestamp) {
    const arrival = this.consumes.length;
    this.consumes.push([timestamp, arrival, amount]);
    return this.replay(timestamp, arrival)[1];
  }
  getBalance(timestamp) { return this.replay(timestamp)[0]; }
}
function solve(operations, args) {
  const system = new CreditSystem(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = system[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.CreditSystem = CreditSystem;
