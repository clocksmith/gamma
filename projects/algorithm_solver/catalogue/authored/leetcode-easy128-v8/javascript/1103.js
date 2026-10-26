'use strict';

// 1103. Distribute Candies to People (Easy).
// Specification: https://leetcode.com/problems/distribute-candies-to-people/description/
// O(num_people + sqrt(candies)) time, O(num_people) space; circulate increasing gifts.
function solve(candies, numPeople) {
  const result = new Array(numPeople).fill(0);
  let remaining = candies;
  let gift = 1;
  while (remaining > 0) {
    const given = Math.min(gift, remaining);
    result[(gift - 1) % numPeople] += given;
    remaining -= given;
    gift++;
  }
  return result;
}

const distributeCandies = solve;
class Solution {
  distributeCandies(candies, numPeople) { return solve(candies, numPeople); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distributeCandies };
