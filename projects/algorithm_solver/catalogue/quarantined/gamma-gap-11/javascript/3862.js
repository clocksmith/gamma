'use strict';

// 3862. Find the Smallest Balanced Index.
// O(n) time and O(1) space; positive suffix products saturate above every possible prefix sum, without overflowing.
function solve(nums) {
  let left = 0;
  for (const value of nums) left += value;
  const cap = left + 1;
  let product = 1;
  let answer = -1;
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    left -= nums[index];
    if (left === product) answer = index;
    product = product > Math.floor((cap - 1) / nums[index]) ? cap : product * nums[index];
  }
  return answer;
}

const smallestBalancedIndex = solve;
class Solution {
  smallestBalancedIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestBalancedIndex };
