// Original candidate implementation. Contract: https://leetcode.com/problems/widest-pair-of-indices-with-equal-range-sum/
"use strict";

function solve(nums1, nums2) {
  const first = new Map([[0, -1]]);
  let delta = 0;
  let answer = 0;
  for (let index = 0; index < nums1.length; index++) {
    delta += nums1[index] - nums2[index];
    if (first.has(delta)) {
      answer = Math.max(answer, index - first.get(delta));
    } else {
      first.set(delta, index);
    }
  }
  return answer;
}

module.exports = solve;
