'use strict';
// 295. Find Median from Data Stream.
class Heap {
  constructor(compare) { this.data = []; this.compare = compare; }
  push(value) { const d = this.data; d.push(value); let i = d.length - 1;
    while (i) { const p = Math.floor((i - 1) / 2); if (!this.compare(d[i], d[p])) break; [d[i], d[p]] = [d[p], d[i]]; i = p; } }
  pop() { const top = this.data[0]; const last = this.data.pop(); if (this.data.length) { this.data[0] = last; let i = 0;
    while (true) { let b = i; const l = i * 2 + 1; const r = l + 1;
      if (l < this.data.length && this.compare(this.data[l], this.data[b])) b = l;
      if (r < this.data.length && this.compare(this.data[r], this.data[b])) b = r;
      if (b === i) break; [this.data[i], this.data[b]] = [this.data[b], this.data[i]]; i = b; } } return top; }
  peek() { return this.data[0]; }
  get size() { return this.data.length; }
}
class MedianFinder {
  constructor() { this.lower = new Heap((a, b) => a > b); this.upper = new Heap((a, b) => a < b); }
  addNum(num) {
    this.lower.push(num); this.upper.push(this.lower.pop());
    if (this.upper.size > this.lower.size) this.lower.push(this.upper.pop());
  }
  findMedian() { return this.lower.size > this.upper.size ? this.lower.peek() : (this.lower.peek() + this.upper.peek()) / 2; }
}
function solve(operations, args) {
  const finder = new MedianFinder();
  return operations.map((operation, index) => operation === 'MedianFinder' ? null : finder[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, MedianFinder };
