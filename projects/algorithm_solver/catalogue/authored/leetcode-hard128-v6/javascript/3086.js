'use strict';

// 3086. Minimum Moves to Pick K Ones.
// Use up to three adjacent ones cheaply, otherwise gather a median window and create the remainder; O(n) time and space. Inputs are preserved.

function solve(nums, k, maxChanges) {
  const positions = [];
  let run = 0, longest = 0;
  nums.forEach((value, index) => {
    if (value) { positions.push(index); run += 1; longest = Math.max(longest, run); } else run = 0;
  });
  const nearby = Math.min(k, 3, longest);
  if (maxChanges >= k - nearby) return Math.max(0, nearby - 1) + 2 * (k - nearby);
  const required = k - maxChanges, prefix = [0];
  for (const position of positions) prefix.push(prefix[prefix.length - 1] + position);
  let answer = Infinity;
  for (let left = 0; left + required <= positions.length; left += 1) {
    const right = left + required, middle = Math.floor((left + right - 1) / 2);
    const distance = positions[middle] * (middle - left) - prefix[middle] + prefix[left] + prefix[right] - prefix[middle + 1] - positions[middle] * (right - middle - 1);
    answer = Math.min(answer, distance + 2 * maxChanges);
  }
  return answer;
}

const minimumMoves = solve;
class Solution {
  minimumMoves(nums, k, maxChanges) { return solve(nums, k, maxChanges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMoves };
