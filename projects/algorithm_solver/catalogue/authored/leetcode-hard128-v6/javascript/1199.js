'use strict';

// 1199. Minimum Time to Build Blocks.
// Combine the two earliest-finishing branches in a min-heap; O(n log n) time, O(n) space. Inputs are preserved.

class MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }
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
    const answer = items[0];
    const last = items.pop();
    if (items.length === 0) return answer;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.compare(items[child + 1], items[child]) < 0) child += 1;
      if (this.compare(last, items[child]) <= 0) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = last;
    return answer;
  }
}

function solve(blocks, split) {
  const heap = new MinHeap();
  for (const time of blocks) heap.push(time);
  while (heap.items.length > 1) {
    heap.pop();
    const later = heap.pop();
    heap.push(later + split);
  }
  return heap.pop();
}

const minBuildTime = solve;
class Solution {
  minBuildTime(blocks, split) { return solve(blocks, split); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minBuildTime };
