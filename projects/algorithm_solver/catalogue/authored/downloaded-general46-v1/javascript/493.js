'use strict';

// 493. Reverse Pairs (Hard).
// Specification: https://leetcode.com/problems/reverse-pairs/description/
function solve(nums) {
  let count = 0;
  function mergeSort(values) {
    if (values.length <= 1) return values;
    const mid = Math.floor(values.length / 2);
    const left = mergeSort(values.slice(0, mid));
    const right = mergeSort(values.slice(mid));
    let j = 0;
    for (const value of left) {
      while (j < right.length && value > 2 * right[j]) j++;
      count += j;
    }
    const merged = [];
    let i = 0; let k = 0;
    while (i < left.length && k < right.length) { if (left[i] <= right[k]) merged.push(left[i++]); else merged.push(right[k++]); }
    while (i < left.length) merged.push(left[i++]);
    while (k < right.length) merged.push(right[k++]);
    return merged;
  }
  mergeSort(nums.slice());
  return count;
}
const reversePairs = solve;
class Solution { reversePairs(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reversePairs };
