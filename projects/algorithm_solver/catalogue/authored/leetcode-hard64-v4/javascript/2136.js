'use strict';

// 2136. Earliest Possible Day of Full Bloom. Plant in nonincreasing growth-time order; O(n log n) time and O(n) space. Inputs are preserved.

function solve(plantTime, growTime) {
  const seeds = plantTime.map((duration, index) => [growTime[index], duration]);
  seeds.sort((a, b) => b[0] - a[0]);
  let planted = 0;
  let answer = 0;
  for (const [growth, duration] of seeds) {
    planted += duration;
    answer = Math.max(answer, planted + growth);
  }
  return answer;
}

const earliestFullBloom = solve;
class Solution {
  earliestFullBloom(plantTime, growTime) { return solve(plantTime, growTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestFullBloom };
