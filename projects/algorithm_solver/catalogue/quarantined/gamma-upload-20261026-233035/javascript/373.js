'use strict';
// 373. Find K Pairs with Smallest Sums.
class Heap {
  constructor() { this.data = []; }
  push(value) { const d = this.data; d.push(value); let i = d.length - 1;
    while (i) { const p = Math.floor((i - 1) / 2); if (d[p][0] <= d[i][0]) break; [d[p], d[i]] = [d[i], d[p]]; i = p; } }
  pop() { const top = this.data[0]; const last = this.data.pop(); if (this.data.length) { this.data[0] = last; let i = 0;
    while (true) { let b = i; const l = i * 2 + 1; const r = l + 1;
      if (l < this.data.length && this.data[l][0] < this.data[b][0]) b = l;
      if (r < this.data.length && this.data[r][0] < this.data[b][0]) b = r;
      if (b === i) break; [this.data[i], this.data[b]] = [this.data[b], this.data[i]]; i = b; } } return top; }
  get size() { return this.data.length; }
}
function solve(nums1, nums2, k) {
  if (!nums1.length || !nums2.length || k === 0) return [];
  const heap = new Heap();
  for (let index = 0; index < Math.min(k, nums1.length); index += 1) heap.push([nums1[index] + nums2[0], index, 0]);
  const result = [];
  while (heap.size && result.length < k) {
    const [, left, right] = heap.pop(); result.push([nums1[left], nums2[right]]);
    if (right + 1 < nums2.length) heap.push([nums1[left] + nums2[right + 1], left, right + 1]);
  }
  return result;
}
const kSmallestPairs = solve;
class Solution { kSmallestPairs(nums1, nums2, k) { return solve(nums1, nums2, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kSmallestPairs };
