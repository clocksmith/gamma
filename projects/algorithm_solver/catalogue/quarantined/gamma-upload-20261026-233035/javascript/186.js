'use strict';
// 186. Reverse Words in a String II.
function reverseRange(values, left, right) {
  while (left < right) { [values[left], values[right]] = [values[right], values[left]]; left += 1; right -= 1; }
}
function solve(s) {
  reverseRange(s, 0, s.length - 1);
  let start = 0;
  for (let end = 0; end <= s.length; end += 1) {
    if (end === s.length || s[end] === ' ') { reverseRange(s, start, end - 1); start = end + 1; }
  }
}
const reverseWords = solve;
class Solution { reverseWords(s) { solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
