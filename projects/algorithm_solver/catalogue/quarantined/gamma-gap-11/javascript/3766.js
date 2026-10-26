'use strict';

// 3766. Minimum Operations to Make Binary Palindrome.
// O(M log M + n log M) time and O(M) space, M the next power of two above max(nums) <= 5000.
function solve(nums) {
  let maximum = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  let limit = 1;
  while (limit <= maximum) limit *= 2;
  const palindromes = [0];
  for (let value = 1; value < limit; value += 1) {
    const digits = value.toString(2);
    if (digits === digits.split('').reverse().join('')) palindromes.push(value);
  }
  const answer = [];
  for (const value of nums) {
    let left = 0;
    let right = palindromes.length;
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (palindromes[middle] < value) left = middle + 1;
      else right = middle;
    }
    let distance = Math.abs(value - palindromes[left - 1]);
    if (left < palindromes.length) distance = Math.min(distance, palindromes[left] - value);
    answer.push(distance);
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
