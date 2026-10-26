'use strict';

// 3703. Remove K-Balanced Substrings.
// O(n + k) time and O(n + k) space; stack-based exact-pattern removal restores prior match state.
function solve(s, k) {
  const pattern = '('.repeat(k) + ')'.repeat(k);
  const length = pattern.length;
  const failure = new Int32Array(length);
  let matched = 0;
  for (let index = 1; index < length; index += 1) {
    while (matched > 0 && pattern[index] !== pattern[matched]) matched = failure[matched - 1];
    if (pattern[index] === pattern[matched]) matched += 1;
    failure[index] = matched;
  }
  const characters = [];
  const states = [];
  matched = 0;
  for (const char of s) {
    while (matched > 0 && char !== pattern[matched]) matched = failure[matched - 1];
    if (char === pattern[matched]) matched += 1;
    characters.push(char);
    states.push(matched);
    if (matched === length) {
      characters.length -= length;
      states.length -= length;
      matched = states.length === 0 ? 0 : states[states.length - 1];
    }
  }
  return characters.join('');
}

const removeSubstring = solve;
class Solution {
  removeSubstring(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeSubstring };
