'use strict';

// 2287. Rearrange Characters to Make Target String (Easy).
// Specification: https://leetcode.com/problems/rearrange-characters-to-make-target-string/description/
// O(n + m) time, O(1) alphabet space; the scarcest required letter limits complete copies.
function solve(s, target) {
  const available = new Array(26).fill(0);
  const required = new Array(26).fill(0);
  for (const character of s) available[character.charCodeAt(0) - 97]++;
  for (const character of target) required[character.charCodeAt(0) - 97]++;
  let copies = s.length;
  for (let letter = 0; letter < 26; letter++) {
    if (required[letter] > 0) copies = Math.min(copies, Math.floor(available[letter] / required[letter]));
  }
  return copies;
}

const rearrangeCharacters = solve;
class Solution {
  rearrangeCharacters(s, target) { return solve(s, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rearrangeCharacters };
