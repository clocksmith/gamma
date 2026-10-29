"use strict";
// Hack2Hire 6907bf40e1919109b6df11ab (Merge K Sorted Price Streams) over an INFERRED spec; qualification unknown.

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

function parse(event) {
  const k = event.indexOf(', ');
  return [Number(event.slice(0, k)), Number(event.slice(k + 2))];
}

function solve(streams) {
  const heap = new Heap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  streams.forEach((s, i) => { if (s.length) heap.push([parse(s[0])[0], i, 0]); });
  const result = [];
  let price = 0;
  while (heap.size) {
    const t = heap.peek()[0];
    while (heap.size && heap.peek()[0] === t) {
      const [, i, j] = heap.pop();
      price += parse(streams[i][j])[1];
      if (j + 1 < streams[i].length) heap.push([parse(streams[i][j + 1])[0], i, j + 1]);
    }
    result.push(`${t}, ${price}`);
  }
  return result;
}

function mergePriceStreams(streams) { return solve(streams); }

module.exports = solve;
module.exports.mergePriceStreams = mergePriceStreams;
