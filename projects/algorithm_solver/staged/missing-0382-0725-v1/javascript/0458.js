'use strict';

// 458. Poor Pigs. Each pig distinguishes completed-rounds plus survival outcomes; avoid logarithm rounding.

function solve(buckets, minutesToDie, minutesToTest) {
  if (buckets <= 1) return 0;
  const states = Math.floor(minutesToTest / minutesToDie) + 1;
  if (states <= 1) throw new RangeError('No completed test round can distinguish multiple buckets.');
  let pigs = 0, capacity = 1;
  while (capacity < buckets) { pigs += 1; capacity *= states; }
  return pigs;
}

const poorPigs = solve;
class Solution {
  poorPigs(buckets, minutesToDie, minutesToTest) { return solve(buckets, minutesToDie, minutesToTest); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, poorPigs };
