'use strict';

// 2940. Find Building Where Alice and Bob Can Meet.
// Activate unresolved queries at their right endpoint and discharge by height; O(n + q log q) time, O(n+q) space. Inputs are preserved.

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

function solve(heights, queries) {
  const attached = heights.map(() => []), answers = Array(queries.length).fill(-1);
  queries.forEach(([a, b], index) => {
    const first = Math.min(a, b), second = Math.max(a, b);
    if (first === second || heights[first] < heights[second]) answers[index] = second;
    else attached[second].push([heights[first], index]);
  });
  const heap = new MinHeap((a, b) => a[0] - b[0] || a[1] - b[1]);
  for (let building = 0; building < heights.length; building += 1) {
    while (heap.items.length > 0 && heap.items[0][0] < heights[building]) answers[heap.pop()[1]] = building;
    for (const request of attached[building]) heap.push(request);
  }
  return answers;
}

const leftmostBuildingQueries = solve;
class Solution {
  leftmostBuildingQueries(heights, queries) { return solve(heights, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, leftmostBuildingQueries };
