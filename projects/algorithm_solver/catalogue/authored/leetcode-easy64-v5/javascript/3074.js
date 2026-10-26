'use strict';

// 3074. Apple Redistribution into Boxes (Easy).
// Specification: https://leetcode.com/problems/apple-redistribution-into-boxes/description/
// O(n + m log m) time, O(m) space; preserve apple and capacity.
function solve(apple, capacity) {
  let remaining = 0;
  for (const count of apple) remaining += count;
  const ordered = capacity.slice().sort((left, right) => right - left);
  for (let index = 0; index < ordered.length; index++) {
    remaining -= ordered[index];
    if (remaining <= 0) return index + 1;
  }
  return -1;
}

const minimumBoxes = solve;
class Solution {
  minimumBoxes(apple, capacity) { return solve(apple, capacity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumBoxes };
