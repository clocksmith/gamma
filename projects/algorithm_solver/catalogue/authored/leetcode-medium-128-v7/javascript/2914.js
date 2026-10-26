'use strict';

// 2914. Minimum Number of Changes to Make Binary String Beautiful: fix exactly one bit in each unequal adjacent pair.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let changes = 0;
  for (let index = 0; index < s.length; index += 2) {
    if (s[index] !== s[index + 1]) changes += 1;
  }
  return changes;
}

const minChanges = solve;
class Solution {
  minChanges(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minChanges };
