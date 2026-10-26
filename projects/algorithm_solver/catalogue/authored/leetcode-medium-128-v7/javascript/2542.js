'use strict';

// 2542. Maximum Subsequence Score: sweep decreasing minima while retaining the k largest eligible first values.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
class BinaryHeap {
  constructor(values = [], before = (left, right) => left < right) {
    this.values = values.slice();
    this.before = before;
    for (let index = Math.floor(this.values.length / 2) - 1; index >= 0; index -= 1) {
      this.siftDown(index);
    }
  }
  get size() { return this.values.length; }
  peek() { return this.values[0]; }
  push(value) {
    const values = this.values;
    let index = values.length;
    values.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.before(value, values[parent])) break;
      values[index] = values[parent];
      index = parent;
    }
    values[index] = value;
  }
  pop() {
    if (this.values.length === 0) return undefined;
    const result = this.values[0];
    const last = this.values.pop();
    if (this.values.length !== 0) {
      this.values[0] = last;
      this.siftDown(0);
    }
    return result;
  }
  siftDown(index) {
    const values = this.values;
    const value = values[index];
    while (2 * index + 1 < values.length) {
      let child = 2 * index + 1;
      if (child + 1 < values.length && this.before(values[child + 1], values[child])) child += 1;
      if (!this.before(values[child], value)) break;
      values[index] = values[child];
      index = child;
    }
    values[index] = value;
  }
}

function solve(nums1, nums2, k) {
  const order = Array.from({ length: nums1.length }, (_, index) => index)
    .sort((left, right) => nums2[right] - nums2[left]);
  const heap = new BinaryHeap();
  let total = 0;
  let best = 0;
  for (const index of order) {
    heap.push(nums1[index]);
    total += nums1[index];
    if (heap.size > k) total -= heap.pop();
    if (heap.size === k) best = Math.max(best, total * nums2[index]);
  }
  return best;
}

const maxScore = solve;
class Solution {
  maxScore(nums1, nums2, k) { return solve(nums1, nums2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
