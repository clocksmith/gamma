'use strict';

// 3635. Earliest Finish Time for Land and Water Rides II.
// Specification: https://leetcode.com/problems/earliest-finish-time-for-land-and-water-rides-ii/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(land count + water count) time, O(1) auxiliary space; evaluate both ride orders.
// Inputs are not modified.

function solve(landStartTime, landDuration, waterStartTime, waterDuration) {
  let landFinished = Infinity, waterFinished = Infinity;
  for (let index = 0; index < landStartTime.length; index++) landFinished = Math.min(landFinished, landStartTime[index] + landDuration[index]);
  for (let index = 0; index < waterStartTime.length; index++) waterFinished = Math.min(waterFinished, waterStartTime[index] + waterDuration[index]);
  let answer = Infinity;
  for (let index = 0; index < waterStartTime.length; index++) answer = Math.min(answer, Math.max(landFinished, waterStartTime[index]) + waterDuration[index]);
  for (let index = 0; index < landStartTime.length; index++) answer = Math.min(answer, Math.max(waterFinished, landStartTime[index]) + landDuration[index]);
  return answer;
}

const earliestFinishTime = solve;
class Solution {
  earliestFinishTime(landStartTime, landDuration, waterStartTime, waterDuration) { return solve(landStartTime, landDuration, waterStartTime, waterDuration); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestFinishTime };
