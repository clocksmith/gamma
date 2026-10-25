'use strict';

// 1400. Construct K Palindrome Strings: bound the number of required palindrome centers.
// O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only.
function solve(s, k) {
  if (k > s.length) return false;
  const frequencies = new Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) {
    frequencies[s.charCodeAt(index) - 97] += 1;
  }
  let oddCount = 0;
  for (const frequency of frequencies) oddCount += frequency % 2;
  return oddCount <= k;
}

const canConstruct = solve;
class Solution {
  canConstruct(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canConstruct };
