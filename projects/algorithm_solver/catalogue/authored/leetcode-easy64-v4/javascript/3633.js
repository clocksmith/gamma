'use strict';

// 3633. Earliest Finish Time for Land and Water Rides I (Easy).
// Specification: https://leetcode.com/problems/earliest-finish-time-for-land-and-water-rides-i/description/
// O(n + m) time, O(1) auxiliary space; earliest first completion dominates; preserve inputs.
function solve(landStartTime, landDuration, waterStartTime, waterDuration) {
  let landFinish = Infinity;
  let waterFinish = Infinity;
  for (let index = 0; index < landStartTime.length; index++) {
    landFinish = Math.min(landFinish, landStartTime[index] + landDuration[index]);
  }
  for (let index = 0; index < waterStartTime.length; index++) {
    waterFinish = Math.min(waterFinish, waterStartTime[index] + waterDuration[index]);
  }
  let result = Infinity;
  for (let index = 0; index < landStartTime.length; index++) {
    result = Math.min(result, Math.max(waterFinish, landStartTime[index]) + landDuration[index]);
  }
  for (let index = 0; index < waterStartTime.length; index++) {
    result = Math.min(result, Math.max(landFinish, waterStartTime[index]) + waterDuration[index]);
  }
  return result;
}

const earliestFinishTime = solve;
class Solution {
  earliestFinishTime(landStartTime, landDuration, waterStartTime, waterDuration) { return solve(landStartTime, landDuration, waterStartTime, waterDuration); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestFinishTime };
