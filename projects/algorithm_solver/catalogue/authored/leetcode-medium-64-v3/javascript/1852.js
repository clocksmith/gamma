'use strict';

// 1852. Distinct Numbers in Each Subarray: maintain frequencies for a fixed-width sliding window.
// O(n) expected time and O(k) auxiliary space excluding output; inputs are read-only.
function solve(nums, k) {
  const counts = new Map();
  const result = [];
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    counts.set(value, (counts.get(value) || 0) + 1);
    if (index >= k) {
      const outgoing = nums[index - k];
      const remaining = counts.get(outgoing) - 1;
      if (remaining === 0) counts.delete(outgoing);
      else counts.set(outgoing, remaining);
    }
    if (index + 1 >= k) result.push(counts.size);
  }
  return result;
}

const distinctNumbers = solve;
class Solution {
  distinctNumbers(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctNumbers };
