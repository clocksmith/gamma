'use strict';

// 1442. Count Triplets That Can Form Two Arrays of Equal XOR (Medium).
// Specification: https://leetcode.com/problems/count-triplets-that-can-form-two-arrays-of-equal-xor/description/
function solve(arr) {
  const prefix = [0];
  for (const value of arr) prefix.push(prefix[prefix.length - 1] ^ value);
  let count = 0;
  for (let i = 0; i < prefix.length; i++) {
    for (let q = i + 2; q < prefix.length; q++) {
      if (prefix[i] === prefix[q]) count += q - i - 1;
    }
  }
  return count;
}
const countTriplets = solve;
class Solution { countTriplets(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTriplets };
