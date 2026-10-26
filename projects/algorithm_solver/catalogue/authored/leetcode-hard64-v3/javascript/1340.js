'use strict';

// 1340. Jump Game V: height-ordered dynamic programming; O(n log n + n*d) time and O(n) space.

function solve(arr, d) {
  const order = Array.from({ length: arr.length }, (_, index) => index);
  order.sort((a, b) => arr[a] - arr[b]);
  const best = Array(arr.length).fill(1);
  let answer = 1;
  for (const index of order) {
    for (const direction of [-1, 1]) {
      for (let distance = 1; distance <= d; distance += 1) {
        const neighbor = index + direction * distance;
        if (neighbor < 0 || neighbor >= arr.length || arr[neighbor] >= arr[index]) break;
        best[index] = Math.max(best[index], 1 + best[neighbor]);
      }
    }
    answer = Math.max(answer, best[index]);
  }
  return answer;
}

const maxJumps = solve;
class Solution {
  maxJumps(arr, d) { return solve(arr, d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxJumps };
