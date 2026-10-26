'use strict';

// 2462. Total Cost to Hire K Workers: merge the two candidate frontiers in a cost-then-index heap and refill the chosen side.
// O((c + k) log(c + 1)) time and O(c) auxiliary space for c = min(n, 2 * candidates); inputs are read-only.
function solve(costs, k, candidates) {
  const heap = [];
  function less(left, right) {
    return left[0] < right[0] || (left[0] === right[0] && left[1] < right[1]);
  }
  function push(entry) {
    let index = heap.length;
    heap.push(entry);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!less(entry, heap[parent])) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = entry;
  }
  function pop() {
    const result = heap[0];
    const last = heap.pop();
    if (heap.length) {
      let index = 0;
      while (2 * index + 1 < heap.length) {
        let child = 2 * index + 1;
        if (child + 1 < heap.length && less(heap[child + 1], heap[child])) child += 1;
        if (!less(heap[child], last)) break;
        heap[index] = heap[child];
        index = child;
      }
      heap[index] = last;
    }
    return result;
  }
  let left = 0;
  let right = costs.length - 1;
  for (let count = 0; count < candidates && left <= right; count += 1) {
    push([costs[left], left, 0]);
    left += 1;
  }
  for (let count = 0; count < candidates && left <= right; count += 1) {
    push([costs[right], right, 1]);
    right -= 1;
  }
  let total = 0;
  for (let count = 0; count < k; count += 1) {
    const [cost, , side] = pop();
    total += cost;
    if (left <= right) {
      if (side === 0) {
        push([costs[left], left, side]);
        left += 1;
      } else {
        push([costs[right], right, side]);
        right -= 1;
      }
    }
  }
  return total;
}

const totalCost = solve;
class Solution {
  totalCost(costs, k, candidates) { return solve(costs, k, candidates); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalCost };
