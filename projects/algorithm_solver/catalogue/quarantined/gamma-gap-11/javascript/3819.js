'use strict';

// 3819. Rotate Non Negative Elements.
// O(n) time and space; left rotation of nonnegative positions in a fresh result.
function solve(nums, k) {
  const values = nums.filter(value => value >= 0);
  const result = nums.slice();
  if (values.length === 0) return result;
  const shift = k % values.length;
  let cursor = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] >= 0) {
      result[index] = values[(cursor + shift) % values.length];
      cursor += 1;
    }
  }
  return result;
}

const rotateElements = solve;
class Solution {
  rotateElements(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotateElements };
