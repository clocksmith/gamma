'use strict';

// 2386. Find the K-Sum of an Array. Enumerate excluded absolute-value sums with a minimum heap; O(n log n+k log k) time and O(n+k) space. Inputs are preserved.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }

  get size() { return this.items.length; }
  peek() { return this.items[0]; }

  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }

  pop() {
    const items = this.items;
    const result = items[0];
    const value = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], value)) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = value;
    return result;
  }
}

function solve(nums, k) {
  let maximum = 0;
  for (const value of nums) if (value > 0) maximum += value;
  const values = nums.map(value => Math.abs(value)).sort((a, b) => a - b);
  const heap = new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  heap.push([0, 0]);
  let loss = 0;
  for (let rank = 0; rank < k; rank += 1) {
    const state = heap.pop();
    loss = state[0];
    const index = state[1];
    if (rank + 1 === k) break;
    if (index < values.length) {
      heap.push([loss + values[index], index + 1]);
      if (index > 0) heap.push([loss + values[index] - values[index - 1], index + 1]);
    }
  }
  return maximum - loss;
}

const kSum = solve;
class Solution {
  kSum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kSum };
