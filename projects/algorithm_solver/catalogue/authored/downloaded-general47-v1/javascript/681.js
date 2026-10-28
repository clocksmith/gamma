'use strict';

// 681. Next Closest Time (Medium).
// Specification: https://leetcode.com/problems/next-closest-time/description/
function solve(time) {
  const digits = new Set([...time].filter((ch) => ch !== ':'));
  const start = Number(time.slice(0, 2)) * 60 + Number(time.slice(3, 5));
  for (let delta = 1; delta <= 1440; delta++) {
    const total = (start + delta) % 1440;
    const text = String(Math.floor(total / 60)).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
    if ([...text].filter((ch) => ch !== ':').every((ch) => digits.has(ch))) return text;
  }
  return time;
}
const nextClosestTime = solve;
class Solution { nextClosestTime(time) { return solve(time); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextClosestTime };
