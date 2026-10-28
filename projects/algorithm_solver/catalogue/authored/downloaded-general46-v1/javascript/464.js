'use strict';

// 464. Can I Win (Medium).
// Specification: https://leetcode.com/problems/can-i-win/description/
function solve(maxChoosableInteger, desiredTotal) {
  if (desiredTotal <= 0) return true;
  const total = maxChoosableInteger * (maxChoosableInteger + 1) / 2;
  if (total < desiredTotal) return false;
  if (maxChoosableInteger >= desiredTotal) return true;
  const memo = new Map();
  function canWin(used, remaining) {
    const key = used + ',' + remaining;
    if (memo.has(key)) return memo.get(key);
    let result = false;
    for (let choice = 1; choice <= maxChoosableInteger; choice++) {
      if ((used >> (choice - 1)) & 1) continue;
      if (choice >= remaining || !canWin(used | (1 << (choice - 1)), remaining - choice)) { result = true; break; }
    }
    memo.set(key, result);
    return result;
  }
  return canWin(0, desiredTotal);
}
const canIWin = solve;
class Solution { canIWin(maxChoosableInteger, desiredTotal) { return solve(maxChoosableInteger, desiredTotal); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canIWin };
