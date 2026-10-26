'use strict';

// 2398. Maximum Number of Robots Within Budget. Sliding window with a monotonic maximum queue; O(n) time and O(n) space. Inputs are preserved.

function solve(chargeTimes, runningCosts, budget) {
  const maximums = [];
  let head = 0;
  let left = 0;
  let running = 0;
  let answer = 0;
  for (let right = 0; right < chargeTimes.length; right += 1) {
    while (maximums.length > head && chargeTimes[maximums[maximums.length - 1]] <= chargeTimes[right]) maximums.pop();
    maximums.push(right);
    running += runningCosts[right];
    while (left <= right && chargeTimes[maximums[head]] + (right - left + 1) * running > budget) {
      if (maximums[head] === left) head += 1;
      running -= runningCosts[left];
      left += 1;
    }
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const maximumRobots = solve;
class Solution {
  maximumRobots(chargeTimes, runningCosts, budget) { return solve(chargeTimes, runningCosts, budget); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumRobots };
