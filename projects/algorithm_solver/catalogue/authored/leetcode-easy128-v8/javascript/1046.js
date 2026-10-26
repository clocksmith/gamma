'use strict';

// 1046. Last Stone Weight (Easy).
// Specification: https://leetcode.com/problems/last-stone-weight/description/
// O(n log n) time, O(n) space; repeatedly remove the two largest stones from a max heap.
function solve(stones) {
  const heap = [];
  function push(value) {
    let index = heap.length;
    heap.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (heap[parent] >= value) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = value;
  }
  function pop() {
    const largest = heap[0];
    const last = heap.pop();
    if (heap.length === 0) return largest;
    let index = 0;
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] > heap[child]) child++;
      if (heap[child] <= last) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = last;
    return largest;
  }
  for (const stone of stones) push(stone);
  while (heap.length > 1) {
    const largest = pop();
    const second = pop();
    if (largest > second) push(largest - second);
  }
  return heap.length === 0 ? 0 : heap[0];
}

const lastStoneWeight = solve;
class Solution {
  lastStoneWeight(stones) { return solve(stones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lastStoneWeight };
