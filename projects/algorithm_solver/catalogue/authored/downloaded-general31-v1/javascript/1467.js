'use strict';

// 1467. Probability of a Two Boxes Having The Same Number of Distinct Balls (Hard).
// Specification: https://leetcode.com/problems/probability-of-a-two-boxes-having-the-same-number-of-distinct-balls/description/
function comb(n, k) {
  if (k < 0 || k > n) return 0;
  let result = 1;
  for (let i = 1; i <= k; i++) result = result * (n - i + 1) / i;
  return result;
}
function solve(balls) {
  const total = balls.reduce((s, v) => s + v, 0);
  if (total % 2 !== 0) return 0;
  const half = total / 2;
  let favorable = 0;
  function dfs(index, remaining, distinct1, distinct2, ways) {
    if (index === balls.length) {
      if (remaining === 0 && distinct1 === distinct2) favorable += ways;
      return;
    }
    const count = balls[index];
    for (let take = 0; take <= count; take++) {
      if (take > remaining) break;
      const d1 = distinct1 + (take > 0 ? 1 : 0);
      const d2 = distinct2 + (take < count ? 1 : 0);
      dfs(index + 1, remaining - take, d1, d2, ways * comb(count, take));
    }
  }
  dfs(0, half, 0, 0, 1);
  return favorable / comb(total, half);
}
const getProbability = solve;
class Solution { getProbability(balls) { return solve(balls); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getProbability };
