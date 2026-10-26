'use strict';

// 2233. Maximum Product After K Increments: increment a smallest element each time and multiply under the exact modulus.
// O(n + k log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const heap = nums.slice();
  function siftDown(index) {
    const value = heap[index];
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] < heap[child]) child += 1;
      if (heap[child] >= value) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = value;
  }
  for (let index = Math.floor(heap.length / 2) - 1; index >= 0; index -= 1) siftDown(index);
  for (let operation = 0; operation < k; operation += 1) {
    heap[0] += 1;
    siftDown(0);
  }
  const modulus = 1000000007n;
  let result = 1n;
  for (const value of heap) result = result * BigInt(value) % modulus;
  return Number(result);
}

const maximumProduct = solve;
class Solution {
  maximumProduct(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumProduct };
