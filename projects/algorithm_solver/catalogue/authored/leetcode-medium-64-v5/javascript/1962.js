'use strict';

// 1962. Remove Stones to Minimize the Total: repeatedly halve the largest pile in a private max heap.
// O(n + k * log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(piles, k) {
  const heap = piles.slice();
  function siftDown(index) {
    const value = heap[index];
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] > heap[child]) child += 1;
      if (heap[child] <= value) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = value;
  }
  for (let index = Math.floor(heap.length / 2) - 1; index >= 0; index -= 1) siftDown(index);
  let total = 0;
  for (const value of piles) total += value;
  for (let operation = 0; operation < k; operation += 1) {
    const removed = Math.floor(heap[0] / 2);
    if (removed === 0) break;
    total -= removed;
    heap[0] -= removed;
    siftDown(0);
  }
  return total;
}

const minStoneSum = solve;
class Solution {
  minStoneSum(piles, k) { return solve(piles, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minStoneSum };
