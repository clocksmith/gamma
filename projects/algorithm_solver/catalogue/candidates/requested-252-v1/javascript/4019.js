'use strict';

// 4019. Merge Close Characters II.
// Specification: https://leetcode.com/problems/merge-close-characters-ii/description/
// O(n) time and O(n) output space; distances use retained-output indices, preserving leftmost-first deletions. Inputs are preserved.
function solve(s, k) {
  const result = [];
  const last = new Int32Array(26).fill(-1);
  for (const character of s) {
    const code = character.charCodeAt(0) - 97;
    // The retained prefix is already in leftmost-first normal form.
    // A new equal character is the only possible new right endpoint.
    if (last[code] >= 0 && result.length - last[code] <= k) continue;
    last[code] = result.length;
    result.push(character);
  }
  return result.join('');
}

if (typeof module !== 'undefined') module.exports = { solve };
