'use strict';

// 2519. Count the Number of K-Big Indices (Hard).
// Specification: https://leetcode.com/problems/count-the-number-of-k-big-indices/description/
function solve(nums, k) {
  class BIT {
    constructor(n) { this.n = n; this.c = new Array(n + 1).fill(0); }
    update(x, delta) { while (x <= this.n) { this.c[x] += delta; x += x & -x; } }
    query(x) { let s = 0; while (x > 0) { s += this.c[x]; x -= x & -x; } return s; }
  }
  const vals = Array.from(new Set(nums)).sort((a, b) => a - b);
  const rank = new Map(vals.map((v, i) => [v, i + 1]));
  const left = new BIT(vals.length); const right = new BIT(vals.length);
  for (const v of nums) right.update(rank.get(v), 1);
  let ans = 0;
  for (const v of nums) {
    const r = rank.get(v);
    right.update(r, -1);
    if (left.query(r - 1) >= k && right.query(r - 1) >= k) ans++;
    left.update(r, 1);
  }
  return ans;
}
const kBigIndices = solve;
class Solution { kBigIndices(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kBigIndices };
