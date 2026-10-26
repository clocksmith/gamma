'use strict';

// 3389. Minimum Operations to Make Character Frequencies Equal.
// Try each final frequency and account for adjacent-letter transfers with alphabet dynamic programming; O(26*n) time and O(26) space. Input is preserved.

function solve(s) {
  const counts = Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97] += 1;
  let answer = s.length, maximum = 0;
  for (const count of counts) maximum = Math.max(maximum, count);
  for (let target = 1; target <= maximum; target += 1) {
    const best = Array(28).fill(0);
    for (let index = 25; index >= 0; index -= 1) {
      const count = counts[index];
      best[index] = Math.min(count, Math.abs(count - target)) + best[index + 1];
      if (index < 25 && counts[index + 1] < target) {
        const deficit = target - counts[index + 1], excess = Math.max(0, count - target);
        const keep = Math.abs(count - target) + deficit - Math.min(excess, deficit);
        const remove = count + deficit - Math.min(count, deficit);
        best[index] = Math.min(best[index], Math.min(keep, remove) + best[index + 2]);
      }
    }
    answer = Math.min(answer, best[0]);
  }
  return answer;
}

const makeStringGood = solve;
class Solution {
  makeStringGood(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeStringGood };
