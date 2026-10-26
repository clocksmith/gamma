'use strict';

// 1354. Construct Target Array With Multiple Sums: reverse largest-value reductions with a heap; O(n) auxiliary space. Inputs are preserved.

class _MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }

  get size() { return this.items.length; }
  peek() { return this.items[0]; }

  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(items[parent], value) <= 0) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }

  pop() {
    const items = this.items;
    if (items.length === 0) return undefined;
    const result = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let index = 0;
      while (index * 2 + 1 < items.length) {
        let child = index * 2 + 1;
        if (child + 1 < items.length &&
            this.compare(items[child + 1], items[child]) < 0) child += 1;
        if (this.compare(last, items[child]) <= 0) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return result;
  }
}

function solve(target) {
  if (target.length === 1) return target[0] === 1;
  const heap = new _MinHeap();
  let total = 0;
  for (const value of target) {
    heap.push(-value);
    total += value;
  }
  while (true) {
    const largest = -heap.pop();
    const remaining = total - largest;
    if (largest === 1 || remaining === 1) return true;
    if (remaining <= 0 || remaining >= largest) return false;
    const previous = largest % remaining;
    if (previous === 0) return false;
    total = remaining + previous;
    heap.push(-previous);
  }
}

const isPossible = solve;
class Solution {
  isPossible(target) { return solve(target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPossible };
