'use strict';

// 1642. Furthest Building You Can Reach: reserve ladders for the largest climbs seen and pay bricks for smaller climbs.
// O(n log(ladders + 2)) time and O(min(n, ladders + 1)) auxiliary space; inputs are read-only.
function solve(heights, bricks, ladders) {
  const heap = [];
  function push(value) {
    let index = heap.length;
    heap.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (heap[parent] <= value) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = value;
  }
  function pop() {
    const result = heap[0];
    const value = heap.pop();
    if (!heap.length) return result;
    let index = 0;
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] < heap[child]) child += 1;
      if (heap[child] >= value) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = value;
    return result;
  }
  let remaining = bricks;
  for (let index = 0; index + 1 < heights.length; index += 1) {
    const climb = heights[index + 1] - heights[index];
    if (climb <= 0) continue;
    push(climb);
    if (heap.length > ladders) remaining -= pop();
    if (remaining < 0) return index;
  }
  return heights.length - 1;
}

const furthestBuilding = solve;
class Solution {
  furthestBuilding(heights, bricks, ladders) { return solve(heights, bricks, ladders); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, furthestBuilding };
