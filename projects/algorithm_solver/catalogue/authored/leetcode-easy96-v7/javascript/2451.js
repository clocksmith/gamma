'use strict';

// 2451. Odd String Difference (Easy).
// Specification: https://leetcode.com/problems/odd-string-difference/description/
// O(n * m) expected time and space; group by adjacent-letter differences; preserve words.
function solve(words) {
  const groups = new Map();
  for (const word of words) {
    const differences = [];
    for (let index = 1; index < word.length; index++) {
      differences.push(word.charCodeAt(index) - word.charCodeAt(index - 1));
    }
    const signature = differences.join(',');
    if (!groups.has(signature)) groups.set(signature, { word, count: 0 });
    groups.get(signature).count++;
  }
  for (const group of groups.values()) {
    if (group.count === 1) return group.word;
  }
  return '';
}

const oddString = solve;
class Solution {
  oddString(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, oddString };
