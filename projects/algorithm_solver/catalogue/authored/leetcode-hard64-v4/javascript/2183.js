'use strict';

// 2183. Count Array Pairs Divisible by K. Group previous values by gcd(value,k); O(n*(tau(k)+log k)) time and O(tau(k)) space. Inputs are preserved.

function solve(nums, k) {
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  const frequency = new Map();
  let answer = 0;
  for (const value of nums) {
    const common = gcd(value, k);
    for (const [previous, count] of frequency) {
      if (common * previous % k === 0) answer += count;
    }
    frequency.set(common, (frequency.get(common) || 0) + 1);
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
