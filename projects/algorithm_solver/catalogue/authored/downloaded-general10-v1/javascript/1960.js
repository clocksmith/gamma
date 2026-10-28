'use strict';

// 1960. Maximum Product of the Length of Two Palindromic Substrings (Hard).
// Specification: https://leetcode.com/problems/maximum-product-of-the-length-of-two-palindromic-substrings/description/
function solve(s) {
  const n = s.length;
  const pref = new Array(n).fill(0); const suff = new Array(n).fill(0);
  for (let c = 0; c < n; c++) {
    for (const step of [0, 1]) {
      let l = c; let r = c + step;
      while (l >= 0 && r < n && s[l] === s[r]) {
        const len = r - l + 1;
        if (len > pref[r]) pref[r] = len;
        if (len > suff[l]) suff[l] = len;
        l--; r++;
      }
    }
  }
  for (let i = 1; i < n; i++) if (pref[i - 1] > pref[i]) pref[i] = pref[i - 1];
  for (let i = n - 2; i >= 0; i--) if (suff[i + 1] > suff[i]) suff[i] = suff[i + 1];
  let best = 0;
  for (let i = 0; i + 1 < n; i++) best = Math.max(best, pref[i] * suff[i + 1]);
  return best;
}
const maxProduct = solve;
class Solution { maxProduct(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
