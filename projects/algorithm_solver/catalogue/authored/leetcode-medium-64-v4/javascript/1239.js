'use strict';

// 1239. Maximum Length of a Concatenated String with Unique Characters: combine disjoint lowercase-letter masks and discard words with repeated letters.
// O(S + 2^n) time and O(2^n) auxiliary space for the fixed 26-letter alphabet; inputs are read-only.
function solve(arr) {
  const states = [[0, 0]];
  let best = 0;
  for (const word of arr) {
    let mask = 0;
    let valid = true;
    for (const letter of word) {
      const bit = 1 << (letter.charCodeAt(0) - 97);
      if (mask & bit) {
        valid = false;
        break;
      }
      mask |= bit;
    }
    if (!valid) continue;
    const count = states.length;
    for (let index = 0; index < count; index += 1) {
      const [used, length] = states[index];
      if ((used & mask) === 0) {
        const combined = length + word.length;
        states.push([used | mask, combined]);
        best = Math.max(best, combined);
      }
    }
  }
  return best;
}

const maxLength = solve;
class Solution {
  maxLength(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxLength };
