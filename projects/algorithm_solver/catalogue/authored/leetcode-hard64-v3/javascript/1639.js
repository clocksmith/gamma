'use strict';

// 1639. Number of Ways to Form a Target String Given a Dictionary: column counts and backward target DP; O(columns*(words+target length)) time and O(target length) space.

function solve(words, target) {
  const modulus = 1000000007;
  const ways = Array(target.length + 1).fill(0);
  ways[0] = 1;
  for (let column = 0; column < words[0].length; column += 1) {
    const frequency = Array(26).fill(0);
    for (const word of words) frequency[word.charCodeAt(column) - 97] += 1;
    for (let length = Math.min(target.length, column + 1); length > 0; length -= 1) {
      const count = frequency[target.charCodeAt(length - 1) - 97];
      ways[length] = (ways[length] + ways[length - 1] * count) % modulus;
    }
  }
  return ways[target.length];
}

const numWays = solve;
class Solution {
  numWays(words, target) { return solve(words, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numWays };
