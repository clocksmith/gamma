"use strict";
// Hack2Hire 6945c7632c048134ada834fb (Chat Message Range Merge, variant 2) over an INFERRED spec; qualification unknown.
function solve(pages) {
  // Min-heap of page numbers keyed by the id at each page's cursor (ties by page number).
  const offset = new Int32Array(pages.length), heap = [];
  const key = number => pages[number][offset[number]][0];
  const less = (a, b) => key(a) < key(b) || (key(a) === key(b) && a < b);
  const siftDown = i => {
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && less(heap[l], heap[m])) m = l;
      if (r < heap.length && less(heap[r], heap[m])) m = r;
      if (m === i) return;
      const t = heap[i]; heap[i] = heap[m]; heap[m] = t;
      i = m;
    }
  };
  pages.forEach((page, number) => { if (page.length) heap.push(number); });
  for (let i = (heap.length >> 1) - 1; i >= 0; i--) siftDown(i);
  const result = [];
  while (heap.length) {
    const number = heap[0], message = pages[number][offset[number]];
    if (!result.length || result[result.length - 1][0] !== message[0]) result.push([message[0], message[1]]);
    offset[number]++;
    if (offset[number] === pages[number].length) { const last = heap.pop(); if (heap.length) heap[0] = last; }
    siftDown(0);
  }
  return result;
}
function mergePages(pages) { return solve(pages); }
module.exports = solve;
module.exports.mergePages = mergePages;
