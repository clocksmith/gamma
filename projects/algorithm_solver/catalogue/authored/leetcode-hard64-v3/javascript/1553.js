'use strict';

// 1553. Minimum Number of Days to Eat N Oranges: memoized division states; O(log(n+1)^2) time and space.

function solve(n) {
  const memo = new Map([[0, 0], [1, 1]]);
  function days(remaining) {
    if (memo.has(remaining)) return memo.get(remaining);
    const answer = 1 + Math.min(remaining % 2 + days(Math.floor(remaining / 2)),
                                remaining % 3 + days(Math.floor(remaining / 3)));
    memo.set(remaining, answer);
    return answer;
  }
  return days(n);
}

const minDays = solve;
class Solution {
  minDays(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDays };
