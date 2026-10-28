'use strict';

// 825. Friends Of Appropriate Ages (Medium).
// Specification: https://leetcode.com/problems/friends-of-appropriate-ages/description/
function solve(ages) {
  const freq = new Array(121).fill(0);
  for (const age of ages) freq[age]++;
  let total = 0;
  for (let a = 1; a <= 120; a++) {
    if (freq[a] === 0) continue;
    for (let b = 1; b <= 120; b++) {
      if (freq[b] === 0) continue;
      if (b <= a / 2 + 7) continue;
      if (b > a) continue;
      if (b > 100 && a < 100) continue;
      if (a === b) total += freq[a] * (freq[a] - 1);
      else total += freq[a] * freq[b];
    }
  }
  return total;
}
const numFriendRequests = solve;
class Solution { numFriendRequests(ages) { return solve(ages); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numFriendRequests };
