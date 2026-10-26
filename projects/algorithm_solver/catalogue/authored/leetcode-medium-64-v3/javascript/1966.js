'use strict';

// 1966. Binary Searchable Numbers in an Unsorted Array: require every earlier value to be smaller and every later value larger.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const suffixMin = new Array(nums.length + 1).fill(Infinity);
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    suffixMin[index] = Math.min(nums[index], suffixMin[index + 1]);
  }
  let prefixMax = -Infinity;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    if (prefixMax < value && value < suffixMin[index + 1]) answer += 1;
    prefixMax = Math.max(prefixMax, value);
  }
  return answer;
}

const binarySearchableNumbers = solve;
class Solution {
  binarySearchableNumbers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, binarySearchableNumbers };
