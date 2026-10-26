'use strict';

// 506. Relative Ranks (Easy).
// Specification: https://leetcode.com/problems/relative-ranks/description/
// O(n log n) time, O(n) space; rank distinct scores without mutating their original order.
function solve(score) {
  const order = Array.from({ length: score.length }, (_, index) => index);
  order.sort((a, b) => score[b] - score[a]);
  const medals = ['Gold Medal', 'Silver Medal', 'Bronze Medal'];
  const result = new Array(score.length);
  for (let rank = 0; rank < order.length; rank++) {
    result[order[rank]] = rank < 3 ? medals[rank] : String(rank + 1);
  }
  return result;
}

const findRelativeRanks = solve;
class Solution {
  findRelativeRanks(score) { return solve(score); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRelativeRanks };
