'use strict';

// 135. Candy (Hard).
// Specification: https://leetcode.com/problems/candy/description/
function solve(ratings) {
  const n = ratings.length;
  const candies = new Array(n).fill(1);
  for (let i = 1; i < n; i++) { if (ratings[i] > ratings[i - 1]) candies[i] = candies[i - 1] + 1; }
  for (let i = n - 2; i >= 0; i--) { if (ratings[i] > ratings[i + 1]) candies[i] = Math.max(candies[i], candies[i + 1] + 1); }
  return candies.reduce((sum, value) => sum + value, 0);
}
const candy = solve;
class Solution { candy(ratings) { return solve(ratings); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, candy };
