'use strict';

// 3720. Lexicographically Smallest Permutation Greater Than Target.
// O(26n) time and O(n) space; keep the longest feasible equal prefix, then take the smallest increase.
function solve(s, target) {
  const counts = new Int32Array(26);
  for (const char of s) counts[char.charCodeAt(0) - 97] += 1;
  const prefix = [];
  let position = 0;
  while (position < target.length && counts[target.charCodeAt(position) - 97] > 0) {
    counts[target.charCodeAt(position) - 97] -= 1;
    prefix.push(target[position]);
    position += 1;
  }
  while (true) {
    if (position < target.length) {
      for (let digit = target.charCodeAt(position) - 96; digit < 26; digit += 1) {
        if (counts[digit] === 0) continue;
        counts[digit] -= 1;
        const suffix = [];
        for (let value = 0; value < 26; value += 1) suffix.push(String.fromCharCode(97 + value).repeat(counts[value]));
        return prefix.join('') + String.fromCharCode(97 + digit) + suffix.join('');
      }
    }
    if (prefix.length === 0) return '';
    position -= 1;
    const restored = prefix.pop();
    counts[restored.charCodeAt(0) - 97] += 1;
  }
}

const lexGreaterPermutation = solve;
class Solution {
  lexGreaterPermutation(s, target) { return solve(s, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexGreaterPermutation };
