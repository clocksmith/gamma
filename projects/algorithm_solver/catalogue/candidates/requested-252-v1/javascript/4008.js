'use strict';

// 4008. Minimum Initial Strength to Defeat All Monsters.
// Specification: https://leetcode.com/problems/minimum-initial-strength-to-defeat-all-monsters/description/
// O(n+q) time and O(n) space; bonuses enable a fight but never replenish strength. Inputs are preserved.
function solve(monsters, boosts) {
  const difference = new Float64Array(monsters.length + 1);
  for (const [left, right, value] of boosts) { difference[left] += value; difference[right + 1] -= value; }
  let bonus = 0;
  let consumed = 0;
  let answer = 0;
  for (let index = 0; index < monsters.length; index++) {
    bonus += difference[index];
    const needed = monsters[index] - bonus;
    if (needed > 0) answer = Math.max(answer, consumed + needed);
    consumed += monsters[index];
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
