'use strict';

// 2657. Find the Prefix Common Array of Two Arrays: count each permutation value when its second cross-array occurrence arrives.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(A, B) {
  const counts = new Uint8Array(A.length + 1);
  const result = [];
  let common = 0;
  for (let index = 0; index < A.length; index += 1) {
    counts[A[index]] += 1;
    if (counts[A[index]] === 2) common += 1;
    counts[B[index]] += 1;
    if (counts[B[index]] === 2) common += 1;
    result.push(common);
  }
  return result;
}

const findThePrefixCommonArray = solve;
class Solution {
  findThePrefixCommonArray(A, B) { return solve(A, B); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findThePrefixCommonArray };
