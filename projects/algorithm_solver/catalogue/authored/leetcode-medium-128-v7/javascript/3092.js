'use strict';

// 3092. Most Frequent IDs: keep current counts and discard outdated maximum-heap records lazily.
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

function solve(nums, freq) {
  const counts = new Map();
  const heap = new BinaryHeap([], (left, right) => left[0] > right[0]
    || (left[0] === right[0] && left[1] < right[1]));
  const result = [];
  for (let index = 0; index < nums.length; index += 1) {
    const identity = nums[index];
    const current = (counts.get(identity) || 0) + freq[index];
    counts.set(identity, current);
    heap.push([current, identity]);
    while (heap.size && heap.peek()[0] !== counts.get(heap.peek()[1])) heap.pop();
    result.push(heap.size ? heap.peek()[0] : 0);
  }
  return result;
}

const mostFrequentIDs = solve;
class Solution {
  mostFrequentIDs(nums, freq) { return solve(nums, freq); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostFrequentIDs };
