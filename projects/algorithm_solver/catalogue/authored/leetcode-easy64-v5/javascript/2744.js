'use strict';

// 2744. Find Maximum Number of String Pairs (Easy).
// Specification: https://leetcode.com/problems/find-maximum-number-of-string-pairs/description/
// O(n) expected time, O(n) space; inputs contain distinct two-letter words.
function solve(words) {
  const unmatched = new Set();
  let pairs = 0;
  for (const word of words) {
    const reversed = word[1] + word[0];
    if (unmatched.has(reversed)) {
      unmatched.delete(reversed);
      pairs++;
    } else {
      unmatched.add(word);
    }
  }
  return pairs;
}

const maximumNumberOfStringPairs = solve;
class Solution {
  maximumNumberOfStringPairs(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumNumberOfStringPairs };
