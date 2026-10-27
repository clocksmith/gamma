/**
 * 4026. Maximum Gap Between Stations
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-gap-between-stations/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4026.Maximum%20Gap%20Between%20Stations/README_EN.md
 * Complexity: O(|skill|+|station|) time, O(|skill|) space.
 * Earliest prefix and latest suffix maximize each consecutive-worker gap. A valid complete assignment is guaranteed; one worker returns zero.
 */

function solve(skill, station) {
  const count = skill.length, latest = new Int32Array(count);
  let j = station.length - 1;
  for (let i = count - 1; i >= 0; i--) {
    while (station[j] !== skill[i]) j--;
    latest[i] = j--;
  }
  let answer = 0; j = 0;
  for (let i = 0; i + 1 < count; i++) {
    while (station[j] !== skill[i]) j++;
    answer = Math.max(answer, latest[i + 1] - j); j++;
  }
  return answer;
}

function maximumGap(skill, station) {
  return solve(skill, station);
}

class Solution {
  maximumGap(skill, station) {
    return solve(skill, station);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maximumGap, Solution };
}
