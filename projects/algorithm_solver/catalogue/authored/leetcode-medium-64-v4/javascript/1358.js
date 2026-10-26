'use strict';

// 1358. Number of Substrings Containing All Three Characters: count valid starting positions from the last occurrence of each letter.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  const last = [-1, -1, -1];
  let total = 0;
  for (let index = 0; index < s.length; index += 1) {
    last[s.charCodeAt(index) - 97] = index;
    total += Math.min(last[0], last[1], last[2]) + 1;
  }
  return total;
}

const numberOfSubstrings = solve;
class Solution {
  numberOfSubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSubstrings };
