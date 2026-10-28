'use strict';

// 458. Poor Pigs (Hard).
// Specification: https://leetcode.com/problems/poor-pigs/description/
function solve(buckets, minutesToDie, minutesToTest) {
  const states = Math.floor(minutesToTest / minutesToDie) + 1;
  let pigs = 0; let capacity = 1;
  while (capacity < buckets) { capacity *= states; pigs++; }
  return pigs;
}
const poorPigs = solve;
class Solution { poorPigs(buckets, minutesToDie, minutesToTest) { return solve(buckets, minutesToDie, minutesToTest); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, poorPigs };
