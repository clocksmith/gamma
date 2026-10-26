'use strict';

// 1624. Largest Substring Between Two Equal Characters (Easy).
// Specification: https://leetcode.com/problems/largest-substring-between-two-equal-characters/description/
// O(n) time, O(1) space for the lowercase ASCII alphabet.
function solve(s) {
  const firstIndices = new Array(26).fill(-1);
  let longest = -1;
  for (let index = 0; index < s.length; index++) {
    const letter = s.charCodeAt(index) - 97;
    if (firstIndices[letter] === -1) firstIndices[letter] = index;
    else longest = Math.max(longest, index - firstIndices[letter] - 1);
  }
  return longest;
}

const maxLengthBetweenEqualCharacters = solve;
class Solution {
  maxLengthBetweenEqualCharacters(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxLengthBetweenEqualCharacters };
