'use strict';

// 1488. Avoid Flood in The City (Medium).
// Specification: https://leetcode.com/problems/avoid-flood-in-the-city/description/
function solve(rains) {
  const answer = new Array(rains.length).fill(1);
  const lastRain = new Map();
  const dryDays = [];
  for (let day = 0; day < rains.length; day++) {
    if (rains[day] === 0) { dryDays.push(day); continue; }
    const lake = rains[day];
    answer[day] = -1;
    if (lastRain.has(lake)) {
      const previous = lastRain.get(lake);
      let chosen = -1;
      for (let i = 0; i < dryDays.length; i++) {
        if (dryDays[i] > previous) { chosen = i; break; }
      }
      if (chosen === -1) return [];
      answer[dryDays[chosen]] = lake;
      dryDays.splice(chosen, 1);
    }
    lastRain.set(lake, day);
  }
  return answer;
}
const avoidFlood = solve;
class Solution { avoidFlood(rains) { return solve(rains); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, avoidFlood };
