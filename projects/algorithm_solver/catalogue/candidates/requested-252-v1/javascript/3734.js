/**
 * 3734. Lexicographically Smallest Palindromic Permutation Greater Than Target
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/lexicographically-smallest-palindromic-permutation-greater-than-target/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3734.Lexicographically%20Smallest%20Palindromic%20Permutation%20Greater%20Than%20Target/README_EN.md
 * Complexity: O(26n) time; O(n) space.
 * Equal-length lowercase strings; strict comparison; returns empty string when impossible.
 */

function solve(s, target) {
  const counts = Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97] += 1;
  const odd = [];
  for (let i = 0; i < 26; i += 1) if (counts[i] % 2 === 1) odd.push(i);
  if (odd.length > 1) return '';
  const center = odd.length ? String.fromCharCode(97 + odd[0]) : '';
  const remaining = counts.map(count => Math.floor(count / 2)), prefix = [];
  const halfLength = Math.floor(s.length / 2);
  while (prefix.length < halfLength) {
    const index = target.charCodeAt(prefix.length) - 97;
    if (remaining[index] === 0) break;
    remaining[index] -= 1; prefix.push(target[prefix.length]);
  }
  if (prefix.length === halfLength) {
    const left = prefix.join(''), candidate = left + center + prefix.slice().reverse().join('');
    if (candidate > target) return candidate;
  }
  for (let position = prefix.length; position >= 0; position -= 1) {
    if (position < halfLength) {
      for (let index = target.charCodeAt(position) - 96; index < 26; index += 1) {
        if (remaining[index] === 0) continue;
        remaining[index] -= 1;
        let left = prefix.join('') + String.fromCharCode(97 + index);
        for (let letter = 0; letter < 26; letter += 1) left += String.fromCharCode(97 + letter).repeat(remaining[letter]);
        return left + center + left.split('').reverse().join('');
      }
    }
    if (prefix.length === 0) break;
    remaining[prefix.pop().charCodeAt(0) - 97] += 1;
  }
  return '';
}

function lexPalindromicPermutation(s, target) {
  return solve(s, target);
}

class Solution {
  lexPalindromicPermutation(s, target) {
    return solve(s, target);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, lexPalindromicPermutation, Solution };
}
