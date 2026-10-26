'use strict';

// 2163. Minimum Difference in Sums After Removal of Elements. Prefix n-smallest and suffix n-largest heaps; O(n log n) time and O(n) space for 3n values. Inputs are preserved.

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
    const first = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let index = 0;
      while (index * 2 + 1 < items.length) {
        let child = index * 2 + 1;
        if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
        if (!this.less(items[child], last)) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return first;
  }
}

function solve(nums) {
  const size = nums.length / 3;
  const prefix = Array(2 * size).fill(0);
  let heap = new MinHeap((a, b) => a < b);
  let total = 0;
  for (let index = 0; index < 2 * size; index += 1) {
    total += nums[index];
    heap.push(-nums[index]);
    if (heap.size > size) total += heap.pop();
    if (index >= size - 1) prefix[index] = total;
  }
  heap = new MinHeap((a, b) => a < b);
  total = 0;
  let answer = Infinity;
  for (let index = nums.length - 1; index >= size; index -= 1) {
    total += nums[index];
    heap.push(nums[index]);
    if (heap.size > size) total -= heap.pop();
    if (index <= 2 * size) answer = Math.min(answer, prefix[index - 1] - total);
  }
  return answer;
}

const minimumDifference = solve;
class Solution {
  minimumDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDifference };
