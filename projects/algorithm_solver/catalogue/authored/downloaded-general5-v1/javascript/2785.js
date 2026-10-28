'use strict';

// 2785. Sort Vowels in a String (Medium).
// Specification: https://leetcode.com/problems/sort-vowels-in-a-string/description/
function solve(s) {
  const vowels = new Set(['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']);
  const found = [];
  for (const ch of s) if (vowels.has(ch)) found.push(ch);
  found.sort();
  let k = 0;
  return s.split('').map((ch) => (vowels.has(ch) ? found[k++] : ch)).join('');
}
const sortVowels = solve;
class Solution { sortVowels(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortVowels };
