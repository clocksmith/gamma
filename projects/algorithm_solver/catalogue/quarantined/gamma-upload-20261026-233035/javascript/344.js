'use strict';
// 344. Reverse String.
function solve(s) {
  for (let left = 0, right = s.length - 1; left < right; left += 1, right -= 1) {
    [s[left], s[right]] = [s[right], s[left]];
  }
}
const reverseString = solve;
class Solution { reverseString(s) { solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseString };
