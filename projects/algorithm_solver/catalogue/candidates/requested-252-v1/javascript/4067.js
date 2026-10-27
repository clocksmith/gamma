'use strict';

// 4067. Longest Subarray With Restricted Pair Sums.
// Specification: https://leetcode.com/problems/longest-subarray-with-restricted-pair-sums/description/
// O(n*V) time and O(V) space, V=500; three distinct indices, including repeated values. Inputs are preserved.
function solve(nums) {
  const counts = new Int32Array(501);
  function conflicts(value) {
    for (let first = 1; first <= 500; first++) {
      if (counts[first] === 0) continue;
      if (value + first <= 500 && counts[value + first] > 0) return true;
      const second = value - first;
      if (second >= 1 && counts[second] > 0 && (second !== first || counts[first] >= 2)) return true;
    }
    return false;
  }
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right++) {
    while (conflicts(nums[right])) counts[nums[left++]]--;
    counts[nums[right]]++;
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
