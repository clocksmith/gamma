"use strict";
// Hack2Hire 67f5703f83ba2e5f057e6dfb (Prefix Search I) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const before = (a, b) => (a[0] !== b[0] ? a[0] < b[0] : a[1] < b[1]);

// heap holds the k smallest keys seen so far, largest at the root
function offer(heap, key, k) {
  if (heap.length < k) {
    heap.push(key);
    for (let i = heap.length - 1; i > 0;) {
      const up = (i - 1) >> 1;
      if (!before(heap[up], heap[i])) break;
      [heap[up], heap[i]] = [heap[i], heap[up]]; i = up;
    }
  } else if (before(key, heap[0])) {
    heap[0] = key;
    for (let i = 0; ;) {
      const l = 2 * i + 1, r = l + 1;
      let big = i;
      if (l < heap.length && before(heap[big], heap[l])) big = l;
      if (r < heap.length && before(heap[big], heap[r])) big = r;
      if (big === i) break;
      [heap[big], heap[i]] = [heap[i], heap[big]]; i = big;
    }
  }
}

function solve(bizNames, prefix, k) {
  const p = prefix.toLowerCase(), width = p.length, heap = [];
  for (const name of bizNames) {
    const words = name.split(" ");
    for (let i = 0; i < words.length; i++) {
      if (words[i].slice(0, width).toLowerCase() === p) { offer(heap, [i, name], k); break; }
    }
  }
  heap.sort((a, b) => a[0] - b[0] || cmp(a[1], b[1]));
  return heap.map((key) => key[1]);
}

function topKBusinessNames(bizNames, prefix, k) { return solve(bizNames, prefix, k); }

module.exports = solve;
module.exports.topKBusinessNames = topKBusinessNames;
