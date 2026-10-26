'use strict';

// 2325. Decode the Message (Easy).
// Specification: https://leetcode.com/problems/decode-the-message/description/
// O(k + m) time, O(m) result space; map first occurrences of lowercase key letters; keep spaces.
function solve(key, message) {
  const mapping = new Map();
  let next = 0;
  for (const character of key) {
    if (character !== ' ' && !mapping.has(character)) {
      mapping.set(character, String.fromCharCode(97 + next));
      next++;
    }
  }
  const result = [];
  for (const character of message) {
    result.push(character === ' ' ? ' ' : mapping.get(character));
  }
  return result.join('');
}

const decodeMessage = solve;
class Solution {
  decodeMessage(key, message) { return solve(key, message); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decodeMessage };
