'use strict';

// 2840. Check if Strings Can be Made Equal With Operations II: compare character counts separately for even and odd positions.
// O(n) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only.
function solve(s1, s2) {
  const counts = new Int32Array(52);
  for (let index = 0; index < s1.length; index += 1) {
    const offset = 26 * (index % 2);
    counts[offset + s1.charCodeAt(index) - 97] += 1;
    counts[offset + s2.charCodeAt(index) - 97] -= 1;
  }
  return counts.every(count => count === 0);
}

const checkStrings = solve;
class Solution {
  checkStrings(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkStrings };
