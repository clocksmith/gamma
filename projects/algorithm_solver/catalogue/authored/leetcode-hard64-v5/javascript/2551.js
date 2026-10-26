'use strict';

// 2551. Put Marbles in Bags. Compare the largest and smallest adjacent-pair boundary sums; O(n log n) time and O(n) space. Inputs are preserved.

function solve(weights, k) {
  const boundaries = [];
  for (let index = 0; index + 1 < weights.length; index += 1) boundaries.push(weights[index] + weights[index + 1]);
  boundaries.sort((a, b) => a - b);
  let answer = 0;
  for (let index = 0; index < k - 1; index += 1) answer += boundaries[boundaries.length - 1 - index] - boundaries[index];
  return answer;
}

const putMarbles = solve;
class Solution {
  putMarbles(weights, k) { return solve(weights, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, putMarbles };
