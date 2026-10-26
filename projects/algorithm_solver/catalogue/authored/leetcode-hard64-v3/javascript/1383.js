'use strict';

// 1383. Maximum Performance of a Team: descending efficiency and a speed heap; O(n log n + n log k) time, O(n) space; exact products.

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

function solve(n, speed, efficiency, k) {
  const engineers = efficiency.map((value, index) => [value, speed[index]]);
  engineers.sort((a, b) => b[0] - a[0]);
  const heap = new _MinHeap();
  let totalSpeed = 0;
  let answer = 0n;
  for (const [minimumEfficiency, candidateSpeed] of engineers) {
    heap.push(candidateSpeed);
    totalSpeed += candidateSpeed;
    if (heap.size > k) totalSpeed -= heap.pop();
    const performance = BigInt(totalSpeed) * BigInt(minimumEfficiency);
    if (performance > answer) answer = performance;
  }
  return Number(answer % 1000000007n);
}

const maxPerformance = solve;
class Solution {
  maxPerformance(n, speed, efficiency, k) { return solve(n, speed, efficiency, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPerformance };
