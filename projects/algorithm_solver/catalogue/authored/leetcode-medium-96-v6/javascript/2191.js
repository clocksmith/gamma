'use strict';

// 2191. Sort the Jumbled Numbers: sort by mapped digit values and retain original indices for stable ties.
// O(n d + n log n) time and O(n) auxiliary and result space for at most d digits; inputs are read-only.
function solve(mapping, nums) {
  function mapped(value) {
    if (value === 0) return mapping[0];
    let place = 1;
    let result = 0;
    while (value > 0) {
      result += mapping[value % 10] * place;
      value = Math.floor(value / 10);
      place *= 10;
    }
    return result;
  }
  const ordered = nums.map((value, index) => [mapped(value), index, value]);
  ordered.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  return ordered.map(entry => entry[2]);
}

const sortJumbled = solve;
class Solution {
  sortJumbled(mapping, nums) { return solve(mapping, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortJumbled };
