'use strict';

// 2495. Number of Subarrays Having Even Product: subtract all-odd endings from all endings at each position.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let oddRun = 0;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    oddRun = nums[index] % 2 !== 0 ? oddRun + 1 : 0;
    answer += index + 1 - oddRun;
  }
  return answer;
}

const evenProduct = solve;
class Solution {
  evenProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, evenProduct };
