'use strict';

// 1781. Sum of Beauty of All Substrings: extend each starting position while tracking nonzero letter frequencies.
// O(26 * n^2) time and O(26) auxiliary space; inputs are read-only.
function solve(s) {
  let result = 0;
  for (let left = 0; left < s.length; left += 1) {
    const counts = new Array(26).fill(0);
    let largest = 0;
    for (let right = left; right < s.length; right += 1) {
      const letter = s.charCodeAt(right) - 97;
      counts[letter] += 1;
      largest = Math.max(largest, counts[letter]);
      let smallest = s.length;
      for (const count of counts) {
        if (count > 0) smallest = Math.min(smallest, count);
      }
      result += largest - smallest;
    }
  }
  return result;
}

const beautySum = solve;
class Solution {
  beautySum(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautySum };
