'use strict';

// 2002. Maximum Product of the Length of Two Palindromic Subsequences: combine a palindromic mask with the best palindromic submask of its complement.
// O(n * 2^n) time and O(2^n) auxiliary space; inputs are read-only.
function solve(s) {
  const size = 1 << s.length;
  const palindrome = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) {
    const letters = [];
    for (let index = 0; index < s.length; index += 1) {
      if (mask & (1 << index)) letters.push(s[index]);
    }
    let valid = true;
    for (let left = 0, right = letters.length - 1; left < right; left += 1, right -= 1) {
      if (letters[left] !== letters[right]) {
        valid = false;
        break;
      }
    }
    if (valid) palindrome[mask] = letters.length;
  }
  const bestSubset = palindrome.slice();
  for (let index = 0; index < s.length; index += 1) {
    const bit = 1 << index;
    for (let mask = 0; mask < size; mask += 1) {
      if (mask & bit) bestSubset[mask] = Math.max(bestSubset[mask], bestSubset[mask ^ bit]);
    }
  }
  const full = size - 1;
  let result = 0;
  for (let mask = 0; mask < size; mask += 1) {
    result = Math.max(result, palindrome[mask] * bestSubset[full ^ mask]);
  }
  return result;
}

const maxProduct = solve;
class Solution {
  maxProduct(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
