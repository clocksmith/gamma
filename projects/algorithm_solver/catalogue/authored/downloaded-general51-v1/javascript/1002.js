'use strict';

// 1002. Find Common Characters (Easy).
// Specification: https://leetcode.com/problems/find-common-characters/description/
function solve(words) {
  const minCounts = new Array(26).fill(Infinity);
  for (const word of words) {
    const counts = new Array(26).fill(0);
    for (const ch of word) counts[ch.charCodeAt(0) - 97]++;
    for (let i = 0; i < 26; i++) minCounts[i] = Math.min(minCounts[i], counts[i]);
  }
  const result = [];
  for (let i = 0; i < 26; i++) { for (let k = 0; k < minCounts[i]; k++) result.push(String.fromCharCode(97 + i)); }
  return result;
}
const commonChars = solve;
class Solution { commonChars(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, commonChars };
