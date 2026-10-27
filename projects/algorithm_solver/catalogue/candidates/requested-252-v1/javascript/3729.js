/**
 * 3729. Count Distinct Subarrays Divisible by K in Sorted Array
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-distinct-subarrays-divisible-by-k-in-sorted-array/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3729.Count%20Distinct%20Subarrays%20Divisible%20by%20K%20in%20Sorted%20Array/README_EN.md
 * Complexity: O(n + g log k) time for g equal-value runs; O(n) space.
 * Assumes supplied nondecreasing input. Distinctness is by sequence, not endpoint pair; integer counts fit Number.
 */

function solve(nums, k) {
  function gcd(a, b) { while (b !== 0) { const remainder = a % b; a = b; b = remainder; } return a; }
  const counts = new Map([[0, 1]]);
  let remainder = 0, answer = 0;
  for (const value of nums) {
    remainder = (remainder + value) % k;
    answer += counts.get(remainder) || 0;
    counts.set(remainder, (counts.get(remainder) || 0) + 1);
  }
  for (let start = 0; start < nums.length;) {
    let end = start + 1;
    while (end < nums.length && nums[end] === nums[start]) end += 1;
    const length = end - start, period = k / gcd(k, nums[start]);
    const validLengths = Math.floor(length / period);
    answer -= validLengths * length - period * validLengths * (validLengths + 1) / 2;
    start = end;
  }
  return answer;
}

function numGoodSubarrays(nums, k) {
  return solve(nums, k);
}

class Solution {
  numGoodSubarrays(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, numGoodSubarrays, Solution };
}
