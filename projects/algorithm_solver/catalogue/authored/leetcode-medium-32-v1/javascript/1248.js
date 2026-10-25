'use strict';

// 1248. Count Number of Nice Subarrays: count matching odd-prefix totals.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const frequencies = new Array(nums.length + 1).fill(0);
  frequencies[0] = 1;
  let oddCount = 0;
  let answer = 0;
  for (const value of nums) {
    oddCount += value % 2;
    if (oddCount >= k) answer += frequencies[oddCount - k];
    frequencies[oddCount] += 1;
  }
  return answer;
}

const numberOfSubarrays = solve;
class Solution {
  numberOfSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSubarrays };
