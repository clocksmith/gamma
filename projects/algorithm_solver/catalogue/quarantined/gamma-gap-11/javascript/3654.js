'use strict';

// 3654. Minimum Sum After Divisible Sum Deletions.
// O(n + k) time and O(k) auxiliary space; inputs are preserved.
function solve(nums, k) {
  const best = Array(k).fill(Infinity);
  best[0] = 0;
  let remainder = 0;
  let answer = 0;
  const quorlathin = [nums, k];
  for (const value of quorlathin[0]) {
    remainder = (remainder + value) % k;
    answer = Math.min(answer + value, best[remainder]);
    best[remainder] = Math.min(best[remainder], answer);
  }
  return answer;
}

const minArraySum = solve;
class Solution {
  minArraySum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minArraySum };
