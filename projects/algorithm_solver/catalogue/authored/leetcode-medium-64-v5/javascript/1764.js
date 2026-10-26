'use strict';

// 1764. Form Array by Concatenating Subarrays of Another Array: match each group at its earliest available position with a prefix-function search.
// O(n + g) time and O(m) auxiliary space, with g total group elements and m the largest group; inputs are read-only.
function solve(groups, nums) {
  let position = 0;
  for (const group of groups) {
    const failure = new Array(group.length).fill(0);
    let matched = 0;
    for (let index = 1; index < group.length; index += 1) {
      while (matched && group[index] !== group[matched]) matched = failure[matched - 1];
      if (group[index] === group[matched]) matched += 1;
      failure[index] = matched;
    }
    matched = 0;
    while (position < nums.length && matched < group.length) {
      const value = nums[position];
      while (matched && value !== group[matched]) matched = failure[matched - 1];
      if (value === group[matched]) matched += 1;
      position += 1;
    }
    if (matched !== group.length) return false;
  }
  return true;
}

const canChoose = solve;
class Solution {
  canChoose(groups, nums) { return solve(groups, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canChoose };
