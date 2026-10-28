'use strict';

// 966. Vowel Spellchecker (Medium).
// Specification: https://leetcode.com/problems/vowel-spellchecker/description/
function isVowel(ch) { return 'aeiou'.includes(ch); }
function vowelKey(word) { return [...word].map((ch) => isVowel(ch) ? '*' : ch).join(''); }
function solve(wordlist, queries) {
  const exact = new Set(wordlist);
  const lowerMap = new Map(); const vowelMap = new Map();
  for (const word of wordlist) {
    const lower = word.toLowerCase();
    if (!lowerMap.has(lower)) lowerMap.set(lower, word);
    const key = vowelKey(lower);
    if (!vowelMap.has(key)) vowelMap.set(key, word);
  }
  const result = [];
  for (const query of queries) {
    if (exact.has(query)) result.push(query);
    else {
      const lower = query.toLowerCase();
      if (lowerMap.has(lower)) result.push(lowerMap.get(lower));
      else if (vowelMap.has(vowelKey(lower))) result.push(vowelMap.get(vowelKey(lower)));
      else result.push('');
    }
  }
  return result;
}
const spellchecker = solve;
class Solution { spellchecker(wordlist, queries) { return solve(wordlist, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, spellchecker };
