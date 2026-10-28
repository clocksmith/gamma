'use strict';

// 1238. Circular Permutation in Binary Representation (Medium).
// Specification: https://leetcode.com/problems/circular-permutation-in-binary-representation/description/
function solve(n, start) {
  const total = 1 << n;
  const gray = [];
  for (let i = 0; i < total; i++) gray.push(i ^ (i >> 1));
  const index = gray.indexOf(start);
  return gray.slice(index).concat(gray.slice(0, index));
}
const circularPermutation = solve;
class Solution { circularPermutation(n, start) { return solve(n, start); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, circularPermutation };
