'use strict';

// 2426. Number of Pairs Satisfying Inequality.
// O(n log n) time, O(n) space; the answer may exceed int32 but is a safe Number.
function solve(nums1, nums2, diff) {
  const values = nums1.map((value, index) => value - nums2[index]);
  const ordered = Array.from(new Set(values)).sort((a, b) => a - b);
  const rank = new Map();
  for (let index = 0; index < ordered.length; index += 1) rank.set(ordered[index], index + 1);
  const tree = new Int32Array(ordered.length + 1);
  let answer = 0;
  for (const value of values) {
    let low = 0;
    let high = ordered.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (ordered[middle] <= value + diff) low = middle + 1;
      else high = middle;
    }
    for (let index = low; index > 0; index -= index & -index) answer += tree[index];
    for (let index = rank.get(value); index < tree.length; index += index & -index) tree[index] += 1;
  }
  return answer;
}

const numberOfPairs = solve;
class Solution {
  numberOfPairs(nums1, nums2, diff) { return solve(nums1, nums2, diff); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPairs };
