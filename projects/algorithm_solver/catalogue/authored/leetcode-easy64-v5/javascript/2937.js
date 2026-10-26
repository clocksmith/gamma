'use strict';

// 2937. Make Three Strings Equal (Easy).
// Specification: https://leetcode.com/problems/make-three-strings-equal/description/
// O(minimum string length) time, O(1) auxiliary space; preserve all strings.
function solve(s1, s2, s3) {
  const limit = Math.min(s1.length, s2.length, s3.length);
  let common = 0;
  while (common < limit && s1[common] === s2[common] && s1[common] === s3[common]) common++;
  if (common === 0) return -1;
  return s1.length + s2.length + s3.length - 3 * common;
}

const findMinimumOperations = solve;
class Solution {
  findMinimumOperations(s1, s2, s3) { return solve(s1, s2, s3); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinimumOperations };
