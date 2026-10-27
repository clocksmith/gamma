'use strict';

// 620. Not Boring Movies. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. cinema: id, movie, description, rating. Output: all four columns, ordered by descending rating.

function solve(cinema) {
  return cinema.filter(row => row.id % 2 === 1 && row.description != null && row.description !== 'boring')
    .slice().sort((a, b) => b.rating - a.rating)
    .map(({id, movie, description, rating}) => ({id, movie, description, rating}));
}

const notBoringMovies = solve;
class Solution {
  notBoringMovies(cinema) { return solve(cinema); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, notBoringMovies };
