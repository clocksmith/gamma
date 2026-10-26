'use strict';

// 1842. Next Palindrome Using Same Digits.
// Next-permute the left half and mirror it, preserving the center; O(n) time and space.

function solve(num) {
  const half = Math.floor(num.length / 2), digits = num.slice(0, half).split('');
  let pivot = half - 2;
  while (pivot >= 0 && digits[pivot] >= digits[pivot + 1]) pivot -= 1;
  if (pivot < 0) return '';
  let successor = half - 1;
  while (digits[successor] <= digits[pivot]) successor -= 1;
  [digits[pivot], digits[successor]] = [digits[successor], digits[pivot]];
  for (let left = pivot + 1, right = half - 1; left < right; left += 1, right -= 1) [digits[left], digits[right]] = [digits[right], digits[left]];
  const left = digits.join('');
  return left + (num.length % 2 ? num[half] : '') + digits.reverse().join('');
}

const nextPalindrome = solve;
class Solution {
  nextPalindrome(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextPalindrome };
