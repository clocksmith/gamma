'use strict';

// 2813. Maximum Elegance of a K-Length Subsequence (Hard).
// Specification: https://leetcode.com/problems/maximum-elegance-of-a-k-length-subsequence/description/
function solve(items, k) {
  const sorted = items.slice().sort((a, b) => b[0] - a[0]);
  let tot = 0;
  const seen = new Set();
  const dup = [];
  for (let i = 0; i < k; i++) {
    const [p, c] = sorted[i];
    tot += p;
    if (seen.has(c)) dup.push(p); else seen.add(c);
  }
  let ans = tot + seen.size * seen.size;
  for (let i = k; i < sorted.length; i++) {
    const [p, c] = sorted[i];
    if (seen.has(c)) continue;
    if (dup.length === 0) break;
    tot += p - dup.pop();
    seen.add(c);
    ans = Math.max(ans, tot + seen.size * seen.size);
  }
  return ans;
}
const findMaximumElegance = solve;
class Solution {
  findMaximumElegance(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximumElegance };
