'use strict';

// 2268. Minimum Number of Keypresses: assign the most frequent letters to the cheapest nine-key positions.
// O(n + 26 log 26) time and O(26) auxiliary space; inputs are read-only.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const char of s) counts[char.charCodeAt(0) - 97] += 1;
  counts.sort((left, right) => right - left);
  let answer = 0;
  for (let index = 0; index < counts.length; index += 1) answer += counts[index] * (Math.floor(index / 9) + 1);
  return answer;
}

const minimumKeypresses = solve;
class Solution {
  minimumKeypresses(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumKeypresses };
