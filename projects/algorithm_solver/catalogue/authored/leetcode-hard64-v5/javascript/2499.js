'use strict';

// 2499. Minimum Total Cost to Make Arrays Unequal. Balance the dominant equal-position value using the cheapest eligible indices; O(n) time and O(n) space. Inputs are preserved.

function solve(nums1, nums2) {
  const counts = new Map();
  let selected = 0;
  let dominant = null;
  let maximum = 0;
  let answer = 0;
  for (let index = 0; index < nums1.length; index += 1) {
    if (nums1[index] !== nums2[index]) continue;
    selected += 1;
    answer += index;
    const count = (counts.get(nums1[index]) || 0) + 1;
    counts.set(nums1[index], count);
    if (count > maximum) { maximum = count; dominant = nums1[index]; }
  }
  for (let index = 0; index < nums1.length; index += 1) {
    if (selected >= 2 * maximum) return answer;
    if (nums1[index] !== nums2[index] && nums1[index] !== dominant && nums2[index] !== dominant) {
      selected += 1;
      answer += index;
    }
  }
  return selected >= 2 * maximum ? answer : -1;
}

const minimumTotalCost = solve;
class Solution {
  minimumTotalCost(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTotalCost };
