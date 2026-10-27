'use strict';

// 681. Next Closest Time.

function solve(time) {
  const allowed = new Set(time.replace(':', '')), start = Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
  for (let elapsed = 1; elapsed <= 1440; elapsed += 1) {
    const value = (start + elapsed) % 1440;
    const candidate = String(Math.floor(value / 60)).padStart(2, '0') + ':' + String(value % 60).padStart(2, '0');
    if (Array.from(candidate).every(char => char === ':' || allowed.has(char))) return candidate;
  }
  return time;
}

const nextClosestTime = solve;
class Solution {
  nextClosestTime(time) { return solve(time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextClosestTime };
