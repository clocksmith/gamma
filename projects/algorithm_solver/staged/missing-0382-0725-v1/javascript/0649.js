'use strict';

// 649. Dota2 Senate.

function solve(senate) {
  const radiant = [], dire = [];
  for (let i = 0; i < senate.length; i += 1) (senate[i] === 'R' ? radiant : dire).push(i);
  let rHead = 0, dHead = 0;
  while (rHead < radiant.length && dHead < dire.length) {
    const r = radiant[rHead++], d = dire[dHead++];
    if (r < d) radiant.push(r + senate.length); else dire.push(d + senate.length);
  }
  return rHead < radiant.length ? 'Radiant' : 'Dire';
}

const predictPartyVictory = solve;
class Solution {
  predictPartyVictory(senate) { return solve(senate); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, predictPartyVictory };
