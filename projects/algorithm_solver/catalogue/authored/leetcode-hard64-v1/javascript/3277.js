'use strict';

// 3277. Maximum XOR Score Subarray Queries: interval XOR recurrence with a packed range-maximum table.
// O(n^2 + q) time and O(n^2 + q) space. Inputs are preserved.
function solve(nums, queries) {
  const n = nums.length;
  const best = new Array(n);
  let belowScore = new Uint32Array(n);
  for (let left = n - 1; left >= 0; left -= 1) {
    const score = new Uint32Array(n);
    const row = new Uint32Array(n);
    score[left] = nums[left];
    row[left] = nums[left];
    for (let right = left + 1; right < n; right += 1) {
      score[right] = score[right - 1] ^ belowScore[right];
      row[right] = Math.max(score[right], row[right - 1], best[left + 1][right]);
    }
    best[left] = row;
    belowScore = score;
  }
  return queries.map(([left, right]) => best[left][right]);
}

const maximumSubarrayXor = solve;
class Solution {
  maximumSubarrayXor(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSubarrayXor };
