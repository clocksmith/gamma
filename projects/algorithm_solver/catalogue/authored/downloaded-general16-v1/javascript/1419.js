'use strict';

// 1419. Minimum Number of Frogs Croaking (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-frogs-croaking/description/
function solve(croakOfFrogs) {
  const order = { c: 0, r: 1, o: 2, a: 3, k: 4 };
  const counts = [0, 0, 0, 0, 0];
  let active = 0; let best = 0;
  for (const ch of croakOfFrogs) {
    const stage = order[ch];
    if (stage === undefined) return -1;
    if (stage > 0 && counts[stage] >= counts[stage - 1]) return -1;
    counts[stage]++;
    if (stage === 0) { active++; best = Math.max(best, active); }
    if (stage === 4) active--;
  }
  if (active !== 0) return -1;
  for (let i = 1; i < 5; i++) if (counts[i] !== counts[0]) return -1;
  return best;
}
const minNumberOfFrogs = solve;
class Solution { minNumberOfFrogs(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumberOfFrogs };
