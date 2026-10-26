'use strict';

// 3681. Maximum XOR of Subsequences.
// O(30n) time and O(30) auxiliary space; inputs are preserved.
function solve(nums) {
  const basis = Array(30).fill(0);
  for (const value of nums) {
    let current = value;
    for (let bit = 29; bit >= 0; bit -= 1) {
      if ((current & (1 << bit)) !== 0) {
        if (basis[bit] !== 0) current ^= basis[bit];
        else {
          basis[bit] = current;
          break;
        }
      }
    }
  }
  let answer = 0;
  for (let bit = 29; bit >= 0; bit -= 1) answer = Math.max(answer, answer ^ basis[bit]);
  return answer;
}

const maxXorSubsequences = solve;
class Solution {
  maxXorSubsequences(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxXorSubsequences };
