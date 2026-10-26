'use strict';

// 2266. Count Number of Texts: count valid final key groups with a bounded dynamic-programming transition.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(pressedKeys) {
  const modulus = 1000000007;
  const ways = new Array(pressedKeys.length + 1).fill(0);
  ways[0] = 1;
  for (let end = 1; end < ways.length; end += 1) {
    const digit = pressedKeys[end - 1];
    const limit = digit === '7' || digit === '9' ? 4 : 3;
    for (let length = 1; length <= limit; length += 1) {
      if (end < length || pressedKeys[end - length] !== digit) break;
      ways[end] = (ways[end] + ways[end - length]) % modulus;
    }
  }
  return ways[ways.length - 1];
}

const countTexts = solve;
class Solution {
  countTexts(pressedKeys) { return solve(pressedKeys); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTexts };
