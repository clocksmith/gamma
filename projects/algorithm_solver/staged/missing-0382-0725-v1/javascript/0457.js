'use strict';

// 457. Circular Array Loop. Find same-direction cycles excluding self-loops; O(n) total visits, input preserved.

function solve(nums) {
  const n = nums.length, done = Array(n).fill(false);
  for (let start = 0; start < n; start += 1) {
    if (done[start]) continue;
    const positive = nums[start] > 0, local = new Set();
    let node = start;
    while (!done[node] && (nums[node] > 0) === positive) {
      if (local.has(node)) return true;
      local.add(node);
      const next = ((node + nums[node]) % n + n) % n;
      if (next === node) break;
      node = next;
    }
    for (const index of local) done[index] = true;
  }
  return false;
}

const circularArrayLoop = solve;
class Solution {
  circularArrayLoop(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, circularArrayLoop };
