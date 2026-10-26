'use strict';

// 1534. Count Good Triplets (Easy).
// Specification: https://leetcode.com/problems/count-good-triplets/description/
// O(n^3) time, O(1) auxiliary space; count ordered index triples meeting all three bounds.
function solve(arr, a, b, c) {
  let total = 0;
  for (let first = 0; first < arr.length - 2; first++) {
    for (let second = first + 1; second < arr.length - 1; second++) {
      if (Math.abs(arr[first] - arr[second]) > a) continue;
      for (let third = second + 1; third < arr.length; third++) {
        if (Math.abs(arr[second] - arr[third]) <= b && Math.abs(arr[first] - arr[third]) <= c) total++;
      }
    }
  }
  return total;
}

const countGoodTriplets = solve;
class Solution {
  countGoodTriplets(arr, a, b, c) { return solve(arr, a, b, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodTriplets };
