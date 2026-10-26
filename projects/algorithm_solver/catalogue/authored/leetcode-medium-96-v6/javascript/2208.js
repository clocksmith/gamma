'use strict';

// 2208. Minimum Operations to Halve Array Sum: repeatedly halve the largest available value with a max heap.
// O(n + h log n) time and O(n) auxiliary space for h halving operations; inputs are read-only.
function solve(nums) {
  const heap = nums.slice();
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
  let remaining = 0;
  for (const value of nums) remaining += value;
  remaining /= 2;
  let operations = 0;
  while (remaining > 0) {
    const half = heap[0] / 2;
    heap[0] = half;
    siftDown(0);
    remaining -= half;
    operations += 1;
  }
  return operations;
}

const halveArray = solve;
class Solution {
  halveArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, halveArray };
