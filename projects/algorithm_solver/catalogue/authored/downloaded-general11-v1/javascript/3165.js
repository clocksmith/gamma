'use strict';

// 3165. Maximum Sum of Subsequence With Nonadjacent Elements (Hard).
// Specification: https://leetcode.com/problems/maximum-sum-of-subsequence-with-non-adjacent-elements/description/
function solve(nums, queries) {
  const NEG = -1e18;
  const n = nums.length;
  const tree = new Array(4 * n);
  function leaf(v) { return [[0, NEG], [NEG, v]]; }
  function merge(a, b) {
    const c = [[NEG, NEG], [NEG, NEG]];
    for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++)
      for (let x = 0; x < 2; x++) for (let y = 0; y < 2; y++) {
        if (x === 1 && y === 1) continue;
        if (a[i][x] === NEG || b[y][j] === NEG) continue;
        c[i][j] = Math.max(c[i][j], a[i][x] + b[y][j]);
      }
    return c;
  }
  function build(node, l, r) {
    if (l === r) { tree[node] = leaf(nums[l]); return; }
    const mid = (l + r) >> 1;
    build(node * 2, l, mid); build(node * 2 + 1, mid + 1, r);
    tree[node] = merge(tree[node * 2], tree[node * 2 + 1]);
  }
  function update(node, l, r, pos, v) {
    if (l === r) { tree[node] = leaf(v); return; }
    const mid = (l + r) >> 1;
    if (pos <= mid) update(node * 2, l, mid, pos, v);
    else update(node * 2 + 1, mid + 1, r, pos, v);
    tree[node] = merge(tree[node * 2], tree[node * 2 + 1]);
  }
  build(1, 0, n - 1);
  const MOD = 1000000007; let total = 0;
  for (const q of queries) {
    nums[q[0]] = q[1];
    update(1, 0, n - 1, q[0], q[1]);
    const root = tree[1];
    const best = Math.max(root[0][0], root[0][1], root[1][0], root[1][1]);
    total = (total + best) % MOD;
  }
  return total;
}
const maximumSumSubsequence = solve;
class Solution { maximumSumSubsequence(nums, queries) { return solve(nums, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSumSubsequence };
