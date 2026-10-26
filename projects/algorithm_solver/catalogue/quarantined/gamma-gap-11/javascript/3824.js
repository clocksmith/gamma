'use strict';

// 3824. Minimum K to Reduce Array Within Limit.
// O(n log(max(n,M))) time and O(1) auxiliary space; monotone feasibility with unchanged input.
function solve(nums) {
  let low = 1;
  let high = nums.length;
  for (const value of nums) high = Math.max(high, value);
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let operations = 0;
    for (const value of nums) {
      operations += Math.floor((value + middle - 1) / middle);
      if (operations > middle * middle) break;
    }
    if (operations <= middle * middle) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minimumK = solve;
class Solution {
  minimumK(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumK };
