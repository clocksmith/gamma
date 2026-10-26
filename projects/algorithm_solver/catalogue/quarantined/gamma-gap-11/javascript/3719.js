'use strict';

// 3719. Longest Balanced Subarray I.
// O(n^2) expected time and O(n) auxiliary space; parity counts distinct values, not occurrences.
function solve(nums) {
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    const seen = new Set();
    let balance = 0;
    for (let right = left; right < nums.length; right += 1) {
      const value = nums[right];
      if (!seen.has(value)) {
        seen.add(value);
        balance += value % 2 === 0 ? 1 : -1;
      }
      if (balance === 0) answer = Math.max(answer, right - left + 1);
    }
  }
  return answer;
}

const longestBalanced = solve;
class Solution {
  longestBalanced(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestBalanced };
