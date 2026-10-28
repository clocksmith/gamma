'use strict';

// 649. Dota2 Senate (Medium).
// Specification: https://leetcode.com/problems/dota2-senate/description/
function solve(senate) {
  const n = senate.length;
  const radiant = [];
  const dire = [];
  for (let i = 0; i < n; i++) { if (senate[i] === 'R') radiant.push(i); else dire.push(i); }
  while (radiant.length > 0 && dire.length > 0) {
    const r = radiant.shift(); const d = dire.shift();
    if (r < d) radiant.push(r + n);
    else dire.push(d + n);
  }
  return radiant.length > 0 ? 'Radiant' : 'Dire';
}
const predictPartyVictory = solve;
class Solution { predictPartyVictory(senate) { return solve(senate); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, predictPartyVictory };
