'use strict';

// 3297. Count Substrings That Can Be Rearranged to Contain a String I (Medium).
// Specification: https://leetcode.com/problems/count-substrings-that-can-be-rearranged-to-contain-a-string-i/description/
function solve(word1, word2) {
  const need = new Map();
  for (const ch of word2) need.set(ch, (need.get(ch) || 0) + 1);
  const have = new Map();
  let left = 0; let ans = 0;
  function valid() {
    for (const [ch, k] of need) if ((have.get(ch) || 0) < k) return false;
    return true;
  }
  function canRemove(ch) {
    if (!need.has(ch)) return true;
    return (have.get(ch) || 0) - 1 >= need.get(ch);
  }
  for (let right = 0; right < word1.length; right++) {
    const ch = word1[right];
    have.set(ch, (have.get(ch) || 0) + 1);
    while (left <= right && canRemove(word1[left])) {
      const c = word1[left];
      have.set(c, have.get(c) - 1);
      left++;
    }
    if (valid()) ans += left + 1;
  }
  return ans;
}
const validSubstringCount = solve;
class Solution { validSubstringCount(word1, word2) { return solve(word1, word2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSubstringCount };
