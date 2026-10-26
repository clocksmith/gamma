'use strict';

// 2509. Cycle Length Queries in a Tree. Climb larger heap labels to their lowest common ancestor; O(q*n) time and O(1) auxiliary space excluding output. Inputs are preserved.

function solve(n, queries) {
  const answer = [];
  for (const query of queries) {
    let [first, second] = query;
    let length = 1;
    while (first !== second) {
      if (first > second) first = Math.floor(first / 2);
      else second = Math.floor(second / 2);
      length += 1;
    }
    answer.push(length);
  }
  return answer;
}

const cycleLengthQueries = solve;
class Solution {
  cycleLengthQueries(n, queries) { return solve(n, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cycleLengthQueries };
