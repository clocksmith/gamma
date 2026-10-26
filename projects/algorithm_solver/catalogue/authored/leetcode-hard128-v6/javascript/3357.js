'use strict';

// 3357. Minimize the Maximum Adjacent Element Difference.
// Binary-search the difference using extremal replacement values and missing-run feasibility; O(n log V) time and O(1) auxiliary space. Inputs are preserved.

function solve(nums) {
  let lower = 0, minimum = Infinity, maximum = -Infinity;
  for (let index = 1; index < nums.length; index += 1) {
    const first = nums[index - 1], second = nums[index];
    if (first !== -1 && second !== -1) lower = Math.max(lower, Math.abs(first - second));
    else if ((first === -1) !== (second === -1)) {
      const value = Math.max(first, second);
      minimum = Math.min(minimum, value); maximum = Math.max(maximum, value);
    }
  }
  if (minimum === Infinity) return lower;
  function possible(difference) {
    if (maximum - minimum <= 2 * difference) return true;
    const first = minimum + difference, second = maximum - difference;
    let index = 0;
    while (index < nums.length) {
      if (nums[index] !== -1) { index += 1; continue; }
      const start = index;
      while (index < nums.length && nums[index] === -1) index += 1;
      const endpoints = [];
      if (start > 0) endpoints.push(nums[start - 1]);
      if (index < nums.length) endpoints.push(nums[index]);
      if (endpoints.every(value => Math.abs(value - first) <= difference)) continue;
      if (endpoints.every(value => Math.abs(value - second) <= difference)) continue;
      if (index - start < 2 || second - first > difference) return false;
      if (endpoints.some(value => Math.min(Math.abs(value - first), Math.abs(value - second)) > difference)) return false;
    }
    return true;
  }
  let upper = Math.max(lower, maximum - minimum);
  while (lower < upper) {
    const middle = Math.floor((lower + upper) / 2);
    if (possible(middle)) upper = middle;
    else lower = middle + 1;
  }
  return lower;
}

const minDifference = solve;
class Solution {
  minDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDifference };
