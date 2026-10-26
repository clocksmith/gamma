'use strict';

// 2059. Minimum Operations to Convert Number: breadth-first search bounded intermediate states while allowing an out-of-range final result.
// O(B * n) time and O(B) auxiliary space for B = 1001 permitted intermediate values; inputs are read-only.
function solve(nums, start, goal) {
  if (start === goal) return 0;
  const seen = new Uint8Array(1001);
  seen[start] = 1;
  const queue = [start];
  let head = 0;
  let steps = 0;
  while (head < queue.length) {
    const layerEnd = queue.length;
    steps += 1;
    while (head < layerEnd) {
      const current = queue[head++];
      for (const value of nums) {
        for (const candidate of [current + value, current - value, current ^ value]) {
          if (candidate === goal) return steps;
          if (candidate >= 0 && candidate <= 1000 && !seen[candidate]) {
            seen[candidate] = 1;
            queue.push(candidate);
          }
        }
      }
    }
  }
  return -1;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums, start, goal) { return solve(nums, start, goal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
