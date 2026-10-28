'use strict';

// 1344. Angle Between Hands of a Clock (Easy).
// Specification: https://leetcode.com/problems/angle-between-hands-of-a-clock/description/
function solve(hour, minutes) {
  const hourAngle = 30 * (hour % 12) + 0.5 * minutes;
  const minuteAngle = 6 * minutes;
  const diff = Math.abs(hourAngle - minuteAngle);
  return Math.min(diff, 360 - diff);
}
const angleClock = solve;
class Solution { angleClock(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, angleClock };
