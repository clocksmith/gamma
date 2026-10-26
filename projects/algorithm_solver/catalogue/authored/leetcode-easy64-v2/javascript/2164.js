'use strict';

// 2164. Sort Even and Odd Indices Independently (Easy).
// Specification: https://leetcode.com/problems/sort-even-and-odd-indices-independently/description/
// O(n log n) time, O(n) space; sort independent copies and preserve nums.
function solve(nums) {
  const even = [];
  const odd = [];
  for (let index = 0; index < nums.length; index++) {
    if (index % 2 === 0) even.push(nums[index]);
    else odd.push(nums[index]);
  }
  even.sort((left, right) => left - right);
  odd.sort((left, right) => right - left);
  const result = new Array(nums.length);
  for (let index = 0; index < nums.length; index++) {
    const offset = Math.floor(index / 2);
    result[index] = index % 2 === 0 ? even[offset] : odd[offset];
  }
  return result;
}

const sortEvenOdd = solve;
class Solution {
  sortEvenOdd(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortEvenOdd };
