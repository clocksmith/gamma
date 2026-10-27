'use strict';

// 595. Big Countries. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. world: name, continent, area, population, gdp. Output: name, population, area.

function solve(world) {
  return world.filter(row => (row.area != null && row.area >= 3000000) || (row.population != null && row.population >= 25000000))
    .map(row => ({name: row.name, population: row.population, area: row.area}));
}

const bigCountries = solve;
class Solution {
  bigCountries(world) { return solve(world); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bigCountries };
