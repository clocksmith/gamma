'use strict';

// 771. Jewels and Stones (Easy).
// Specification: https://leetcode.com/problems/jewels-and-stones/description/
// O(j + s) expected time, O(j) space; distinguish uppercase and lowercase letters.
function solve(jewels, stones) {
  const valuable = new Set(jewels);
  let result = 0;
  for (const stone of stones) {
    if (valuable.has(stone)) result++;
  }
  return result;
}

const numJewelsInStones = solve;
class Solution {
  numJewelsInStones(jewels, stones) { return solve(jewels, stones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numJewelsInStones };
