'use strict';

// 1431. Kids With the Greatest Number of Candies (Easy).
// Specification: https://leetcode.com/problems/kids-with-the-greatest-number-of-candies/description/
// O(n) time, O(n) output space; preserve candies.
function solve(candies, extraCandies) {
  let greatest = candies[0];
  for (const count of candies) greatest = Math.max(greatest, count);
  return candies.map(count => count + extraCandies >= greatest);
}

const kidsWithCandies = solve;
class Solution {
  kidsWithCandies(candies, extraCandies) { return solve(candies, extraCandies); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kidsWithCandies };
