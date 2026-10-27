'use strict';

// 454. 4Sum II.

function solve(nums1, nums2, nums3, nums4) {
  const counts = new Map();
  for (const a of nums1) for (const b of nums2) counts.set(a + b, (counts.get(a + b) || 0) + 1);
  let answer = 0;
  for (const c of nums3) for (const d of nums4) answer += counts.get(-c - d) || 0;
  return answer;
}

const fourSumCount = solve;
class Solution {
  fourSumCount(nums1, nums2, nums3, nums4) { return solve(nums1, nums2, nums3, nums4); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fourSumCount };
