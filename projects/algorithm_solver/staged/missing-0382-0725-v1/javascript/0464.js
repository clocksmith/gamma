'use strict';

// 464. Can I Win. Memoized minimax over the chosen-number mask.

function solve(maxChoosableInteger, desiredTotal) {
  if (desiredTotal <= 0) return true;
  if (maxChoosableInteger * (maxChoosableInteger + 1) / 2 < desiredTotal) return false;
  const memo = new Map();
  function win(mask, remaining) {
    if (memo.has(mask)) return memo.get(mask);
    for (let value = maxChoosableInteger; value >= 1; value -= 1) {
      const bit = 1 << (value - 1);
      if ((mask & bit) !== 0) continue;
      if (value >= remaining || !win(mask | bit, remaining - value)) { memo.set(mask, true); return true; }
    }
    memo.set(mask, false); return false;
  }
  return win(0, desiredTotal);
}

const canIWin = solve;
class Solution {
  canIWin(maxChoosableInteger, desiredTotal) { return solve(maxChoosableInteger, desiredTotal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canIWin };
