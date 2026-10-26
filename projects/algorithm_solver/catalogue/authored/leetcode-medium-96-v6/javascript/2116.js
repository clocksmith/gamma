'use strict';

// 2116. Check if a Parentheses String Can Be Valid: track the interval of feasible open-parenthesis counts.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, locked) {
  if (s.length % 2) return false;
  let low = 0;
  let high = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (locked[index] === '0') {
      low -= 1;
      high += 1;
    } else if (s[index] === '(') {
      low += 1;
      high += 1;
    } else {
      low -= 1;
      high -= 1;
    }
    if (high < 0) return false;
    low = Math.max(low, 0);
  }
  return low === 0;
}

const canBeValid = solve;
class Solution {
  canBeValid(s, locked) { return solve(s, locked); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canBeValid };
