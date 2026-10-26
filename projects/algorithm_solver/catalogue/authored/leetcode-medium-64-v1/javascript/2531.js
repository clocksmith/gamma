'use strict';

// 2531. Make Number of Distinct Characters Equal: evaluate each available letter swap by its effect on distinct counts.
// O(n + m + 26^2) time and O(1) auxiliary space; inputs are read-only.
function solve(word1, word2) {
  const first = new Array(26).fill(0);
  const second = new Array(26).fill(0);
  for (let index = 0; index < word1.length; index += 1) first[word1.charCodeAt(index) - 97] += 1;
  for (let index = 0; index < word2.length; index += 1) second[word2.charCodeAt(index) - 97] += 1;
  const firstDistinct = first.filter(count => count > 0).length;
  const secondDistinct = second.filter(count => count > 0).length;
  for (let left = 0; left < 26; left += 1) {
    if (first[left] === 0) continue;
    for (let right = 0; right < 26; right += 1) {
      if (second[right] === 0) continue;
      if (left === right) {
        if (firstDistinct === secondDistinct) return true;
        continue;
      }
      const nextFirst = firstDistinct - (first[left] === 1 ? 1 : 0) + (first[right] === 0 ? 1 : 0);
      const nextSecond = secondDistinct - (second[right] === 1 ? 1 : 0) + (second[left] === 0 ? 1 : 0);
      if (nextFirst === nextSecond) return true;
    }
  }
  return false;
}

const isItPossible = solve;
class Solution {
  isItPossible(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isItPossible };
