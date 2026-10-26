'use strict';

// 3755. Find Maximum Balanced XOR Subarray Length.
// O(n) expected time and O(n) space; match both prefix XOR and parity-count balance.
function solve(nums) {
  const earliest = new Map([['0,0', -1]]);
  let combined = 0;
  let balance = 0;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    combined ^= value;
    balance += value % 2 === 0 ? 1 : -1;
    const key = `${combined},${balance}`;
    if (earliest.has(key)) answer = Math.max(answer, index - earliest.get(key));
    else earliest.set(key, index);
  }
  return answer;
}

const maxBalancedSubarray = solve;
class Solution {
  maxBalancedSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBalancedSubarray };
