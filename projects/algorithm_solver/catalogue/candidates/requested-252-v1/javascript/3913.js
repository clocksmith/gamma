/**
 * 3913. Sort Vowels by Frequency
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/sort-vowels-by-frequency/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3913.Sort%20Vowels%20by%20Frequency/README_EN.md
 * Complexity: O(n) time and space (five vowel kinds).
 * Lowercase English; consonant positions fixed. Ties use first occurrence, not alphabetic order.
 */

function solve(s) {
  const counts = new Map();
  const first = new Map();
  for (let index = 0; index < s.length; index += 1) {
    const character = s[index];
    if ('aeiou'.includes(character)) {
      counts.set(character, (counts.get(character) || 0) + 1);
      if (!first.has(character)) first.set(character, index);
    }
  }
  const order = [...counts.keys()].sort((a, b) => counts.get(b) - counts.get(a) || first.get(a) - first.get(b));
  const replacement = order.map(character => character.repeat(counts.get(character))).join('');
  let index = 0;
  return [...s].map(character => counts.has(character) ? replacement[index++] : character).join('');
}

function sortVowels(s) {
  return solve(s);
}

class Solution {
  sortVowels(s) {
    return solve(s);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, sortVowels, Solution };
}
