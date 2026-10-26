'use strict';

// 3660. Jump Game IX.
// O(n) time and O(n) auxiliary space; inputs are preserved.
function solve(nums) {
  const size = nums.length;
  const suffixMinimum = Array(size + 1).fill(Infinity);
  for (let index = size - 1; index >= 0; index -= 1) suffixMinimum[index] = Math.min(nums[index], suffixMinimum[index + 1]);
  const answer = Array(size).fill(0);
  let start = 0;
  let maximum = 0;
  for (let index = 0; index < size; index += 1) {
    maximum = Math.max(maximum, nums[index]);
    if (maximum <= suffixMinimum[index + 1]) {
      for (let position = start; position <= index; position += 1) answer[position] = maximum;
      start = index + 1;
    }
  }
  return answer;
}

const maxValue = solve;
class Solution {
  maxValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValue };
