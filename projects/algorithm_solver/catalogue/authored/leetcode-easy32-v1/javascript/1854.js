'use strict';

// 1854. Maximum Population Year (Easy).
// Specification: https://leetcode.com/problems/maximum-population-year/description/
// O(n + Y) time, O(Y) space; Y = 100 supported years. Death is exclusive.
function solve(logs) {
  const firstYear = 1950;
  const lastYear = 2050;
  const changes = new Array(lastYear - firstYear + 1).fill(0);
  for (const [birth, death] of logs) {
    changes[birth - firstYear]++;
    changes[death - firstYear]--;
  }
  let population = 0;
  let bestPopulation = 0;
  let bestYear = firstYear;
  for (let year = firstYear; year < lastYear; year++) {
    population += changes[year - firstYear];
    if (population > bestPopulation) {
      bestPopulation = population;
      bestYear = year;
    }
  }
  return bestYear;
}

const maximumPopulation = solve;
class Solution {
  maximumPopulation(logs) { return solve(logs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumPopulation };
