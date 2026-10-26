'use strict';

// 2261. K Divisible Elements Subarrays: insert eligible subarrays into a value trie and count only newly created prefixes.
// O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only.
function solve(nums, k, p) {
  const root = new Map();
  let distinct = 0;
  for (let left = 0; left < nums.length; left += 1) {
    let node = root;
    let divisible = 0;
    for (let right = left; right < nums.length; right += 1) {
      const value = nums[right];
      if (value % p === 0) divisible += 1;
      if (divisible > k) break;
      if (!node.has(value)) {
        node.set(value, new Map());
        distinct += 1;
      }
      node = node.get(value);
    }
  }
  return distinct;
}

const countDistinct = solve;
class Solution {
  countDistinct(nums, k, p) { return solve(nums, k, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDistinct };
