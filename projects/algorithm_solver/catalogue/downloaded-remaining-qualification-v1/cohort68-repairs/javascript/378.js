'use strict';

// 378. Kth Smallest Element in a Sorted Matrix (Medium).
// Specification: https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description/
function solve(matrix, k) {
  const heap = matrix.map((row, r) => [row[0], r, 0]);
  function down(start) {
    let at = start;
    while (true) {
      let child = at * 2 + 1;
      if (child >= heap.length) return;
      if (child + 1 < heap.length && heap[child + 1][0] < heap[child][0]) child++;
      if (heap[at][0] <= heap[child][0]) return;
      const item = heap[at]; heap[at] = heap[child]; heap[child] = item; at = child;
    }
  }
  for (let i = Math.floor(heap.length / 2) - 1; i >= 0; i--) down(i);
  let value = 0;
  for (let rank = 0; rank < k; rank++) {
    const item = heap[0]; value = item[0];
    const r = item[1], c = item[2] + 1;
    const replacement = c < matrix[r].length ? [matrix[r][c], r, c] : heap.pop();
    if (heap.length > 0) { heap[0] = replacement; down(0); }
  }
  return value;
}
const kthSmallest = solve;
class Solution { kthSmallest(matrix, k) { return solve(matrix, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallest };
