// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-divisible-triplet-sums/
"use strict";

function solve(nums, d) {
  const left = new Map();
  let answer = 0;
  for (let middle = 0; middle < nums.length; middle++) {
    for (let right = middle + 1; right < nums.length; right++) {
      const remainder = ((-(nums[middle] + nums[right])) % d + d) % d;
      answer += left.get(remainder) || 0;
    }
    const remainder = nums[middle] % d;
    left.set(remainder, (left.get(remainder) || 0) + 1);
  }
  return answer;
}

module.exports = solve;
