'use strict';

// 2530. Maximal Score After Applying K Operations: take the current maximum from a heap and return its rounded-up third.
// O(n + k log n) time and O(n) auxiliary space; inputs are read-only.
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

function solve(nums, k) {
  const heap = new BinaryHeap(nums, (left, right) => left > right);
  let score = 0;
  for (let step = 0; step < k; step += 1) {
    const value = heap.pop();
    score += value;
    heap.push(Math.ceil(value / 3));
  }
  return score;
}

const maxKelements = solve;
class Solution {
  maxKelements(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxKelements };
