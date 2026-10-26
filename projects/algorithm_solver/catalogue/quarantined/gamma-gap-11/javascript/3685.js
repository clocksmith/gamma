'use strict';

// 3685. Subsequence Sum After Capping Elements.
// O(n * k) time and O(n + k) auxiliary space; inputs are preserved.
function solve(nums, k) {
  const n = nums.length;
  const frequency = new Int32Array(n + 1);
  for (const value of nums) frequency[value] += 1;
  const reachable = new Uint8Array(k + 1);
  reachable[0] = 1;
  let remaining = n;
  const answer = [];
  for (let cap = 1; cap <= n; cap += 1) {
    let possible = false;
    const limit = Math.min(remaining, Math.floor(k / cap));
    for (let count = 0; count <= limit; count += 1) {
      if (reachable[k - count * cap]) {
        possible = true;
        break;
      }
    }
    answer.push(possible);
    for (let count = 0; count < frequency[cap]; count += 1) {
      for (let total = k; total >= cap; total -= 1) {
        reachable[total] |= reachable[total - cap];
      }
    }
    remaining -= frequency[cap];
  }
  return answer;
}

const subsequenceSumAfterCapping = solve;
class Solution {
  subsequenceSumAfterCapping(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsequenceSumAfterCapping };
