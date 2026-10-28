'use strict';

// 3265. Count Almost Equal Pairs I (Medium).
// Specification: https://leetcode.com/problems/count-almost-equal-pairs-i/description/
function solve(nums) {
  const maxLen = Math.max(...nums.map((x) => String(x).length));
  const count = new Map();
  let ans = 0;
  for (const num of nums) {
    const digits = String(num).padStart(maxLen, '0').split('');
    const variants = new Set([num]);
    for (let i = 0; i < digits.length; i++) {
      for (let j = i + 1; j < digits.length; j++) {
        const copy = digits.slice();
        const tmp = copy[i]; copy[i] = copy[j]; copy[j] = tmp;
        variants.add(parseInt(copy.join(''), 10));
      }
    }
    for (const v of variants) ans += count.get(v) || 0;
    count.set(num, (count.get(num) || 0) + 1);
  }
  return ans;
}
const countPairs = solve;
class Solution { countPairs(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
