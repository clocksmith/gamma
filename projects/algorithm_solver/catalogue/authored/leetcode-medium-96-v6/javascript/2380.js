'use strict';

// 2380. Time Needed to Rearrange a Binary String: track how zeros ahead and earlier moving ones delay each subsequent one.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let zeros = 0;
  let seconds = 0;
  for (const character of s) {
    if (character === '0') zeros += 1;
    else if (zeros > 0) seconds = Math.max(seconds + 1, zeros);
  }
  return seconds;
}

const secondsToRemoveOccurrences = solve;
class Solution {
  secondsToRemoveOccurrences(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, secondsToRemoveOccurrences };
