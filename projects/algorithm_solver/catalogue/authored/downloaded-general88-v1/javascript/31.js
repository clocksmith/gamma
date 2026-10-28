'use strict';

// 31. Next Permutation (Medium).
// Specification: https://leetcode.com/problems/next-permutation/description/
function solve(nums) {
  const result = nums.slice();
  let pivot = -1;
  for (let i = result.length - 2; i >= 0; i--) { if (result[i] < result[i + 1]) { pivot = i; break; } }
  if (pivot === -1) return result.reverse();
  for (let i = result.length - 1; i > pivot; i--) {
    if (result[i] > result[pivot]) { const tmp = result[i]; result[i] = result[pivot]; result[pivot] = tmp; break; }
  }
  let left = pivot + 1; let right = result.length - 1;
  while (left < right) { const tmp = result[left]; result[left] = result[right]; result[right] = tmp; left++; right--; }
  return result;
}
const nextPermutation = solve;
class Solution { nextPermutation(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextPermutation };
