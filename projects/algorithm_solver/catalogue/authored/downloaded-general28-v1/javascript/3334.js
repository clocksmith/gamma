'use strict';

// 3334. Find the Maximum Factor Score of Array (Medium).
// Specification: https://leetcode.com/problems/find-the-maximum-factor-score-of-array/description/
function solve(nums) {
  function gcd(a, b) { while (b) { const t = a % b; a = b; b = t; } return a; }
  function score(arr) {
    if (arr.length === 0) return 0;
    let g = arr[0]; let l = arr[0];
    for (let i = 1; i < arr.length; i++) {
      g = gcd(g, arr[i]);
      l = l / gcd(l, arr[i]) * arr[i];
    }
    return g * l;
  }
  let best = score(nums);
  for (let i = 0; i < nums.length; i++) {
    const rest = nums.slice(0, i).concat(nums.slice(i + 1));
    best = Math.max(best, score(rest));
  }
  return best;
}
const maxScore = solve;
class Solution { maxScore(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
