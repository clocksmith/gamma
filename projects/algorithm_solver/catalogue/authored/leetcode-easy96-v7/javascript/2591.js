'use strict';

// 2591. Distribute Money to Maximum Children (Easy).
// Specification: https://leetcode.com/problems/distribute-money-to-maximum-children/description/
// O(1) time and space; reserve one dollar each, maximize eights, and repair leftover/four-dollar cases.
function solve(money, children) {
  if (money < children) return -1;
  let extra = money - children;
  let eights = Math.min(children, Math.floor(extra / 7));
  extra -= eights * 7;
  if (eights === children && extra > 0) eights--;
  else if (eights === children - 1 && extra === 3) eights--;
  return eights;
}

const distMoney = solve;
class Solution {
  distMoney(money, children) { return solve(money, children); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distMoney };
