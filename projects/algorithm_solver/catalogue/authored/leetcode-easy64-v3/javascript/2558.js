'use strict';

// 2558. Take Gifts From the Richest Pile (Easy).
// Specification: https://leetcode.com/problems/take-gifts-from-the-richest-pile/description/
// O(n + k log n) time, O(n) space; preserve gifts and maintain a max heap.
function solve(gifts, k) {
  const heap = gifts.slice();
  function siftDown(index) {
    const value = heap[index];
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] > heap[child]) child++;
      if (heap[child] <= value) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = value;
  }
  for (let index = Math.floor(heap.length / 2) - 1; index >= 0; index--) {
    siftDown(index);
  }
  for (let step = 0; step < k && heap[0] > 1; step++) {
    heap[0] = Math.floor(Math.sqrt(heap[0]));
    siftDown(0);
  }
  let total = 0;
  for (const value of heap) total += value;
  return total;
}

const pickGifts = solve;
class Solution {
  pickGifts(gifts, k) { return solve(gifts, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pickGifts };
