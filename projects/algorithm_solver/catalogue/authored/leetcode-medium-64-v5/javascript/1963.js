'use strict';

// 1963. Minimum Number of Swaps to Make the String Balanced: pair unmatched closing brackets two at a time.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let opened = 0;
  let unmatched = 0;
  for (const bracket of s) {
    if (bracket === '[') opened += 1;
    else if (opened > 0) opened -= 1;
    else unmatched += 1;
  }
  return Math.floor((unmatched + 1) / 2);
}

const minSwaps = solve;
class Solution {
  minSwaps(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
