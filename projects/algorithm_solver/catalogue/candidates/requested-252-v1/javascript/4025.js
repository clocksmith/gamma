/**
 * 4025. Minimize the Maximum Waiting Time at Synchronized Traffic Lights
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimize-the-maximum-waiting-time-at-synchronized-traffic-lights/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4025.Minimize%20the%20Maximum%20Waiting%20Time%20at%20Synchronized%20Traffic%20Lights/README_EN.md
 * Complexity: O(|lights|+|arrivalTime|) time, O(1) space.
 * Unlimited simultaneous cars make the longest green phase weakly optimal for every car. Equality with green duration is red.
 */

function solve(period, lights, arrivalTime) {
  let green = 0, answer = 0;
  for (const value of lights) green = Math.max(green, value);
  for (const time of arrivalTime) { const phase = time % period; if (phase >= green) answer = Math.max(answer, period - phase); }
  return answer;
}

function minPenalty(period, lights, arrivalTime) {
  return solve(period, lights, arrivalTime);
}

class Solution {
  minPenalty(period, lights, arrivalTime) {
    return solve(period, lights, arrivalTime);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minPenalty, Solution };
}
