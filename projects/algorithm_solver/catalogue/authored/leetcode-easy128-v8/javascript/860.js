'use strict';

// 860. Lemonade Change (Easy).
// Specification: https://leetcode.com/problems/lemonade-change/description/
// O(n) time, O(1) space; prefer one ten and one five when changing a twenty.
function solve(bills) {
  let fives = 0;
  let tens = 0;
  for (const bill of bills) {
    if (bill === 5) fives++;
    else if (bill === 10) {
      if (fives === 0) return false;
      fives--;
      tens++;
    } else if (tens > 0 && fives > 0) {
      tens--;
      fives--;
    } else if (fives >= 3) {
      fives -= 3;
    } else {
      return false;
    }
  }
  return true;
}

const lemonadeChange = solve;
class Solution {
  lemonadeChange(bills) { return solve(bills); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lemonadeChange };
