"use strict";
// Hack2Hire 6a7f6aa4d713d873ca7adb44 (Find the Most Common Ads, v1); INFERRED spec; qualification unknown.
function weaker(a, b) { return a[0] < b[0] || (a[0] === b[0] && a[1] > b[1]); }
function push(heap, item) {
  heap.push(item);
  for (let i = heap.length - 1; i > 0;) { const p = (i - 1) >> 1; if (!weaker(heap[i], heap[p])) break; [heap[i], heap[p]] = [heap[p], heap[i]]; i = p; }
}
function pop(heap) {
  const top = heap[0], last = heap.pop();
  if (heap.length) {
    heap[0] = last;
    for (let i = 0; ;) {
      const l = 2 * i + 1, r = l + 1; let m = i;
      if (l < heap.length && weaker(heap[l], heap[m])) m = l;
      if (r < heap.length && weaker(heap[r], heap[m])) m = r;
      if (m === i) break; [heap[i], heap[m]] = [heap[m], heap[i]]; i = m;
    }
  }
  return top;
}
function topK(counts, k) {
  const heap = [];
  for (const [ad, count] of counts) {
    const item = [count, ad];
    if (heap.length < k) push(heap, item); else if (weaker(heap[0], item)) { pop(heap); push(heap, item); }
  }
  const out = [];
  while (heap.length) out.push(pop(heap)[1]);
  return out.reverse();
}
function solve(impressions, k) {
  const counts = new Map();
  for (const [, ad] of impressions) counts.set(ad, (counts.get(ad) || 0) + 1);
  return topK(counts, k);
}
function topKAds(impressions, k) { return solve(impressions, k); }
module.exports = solve;
module.exports.topKAds = topKAds;
