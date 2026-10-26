'use strict';

// 2374. Node With Highest Edge Score: sum incoming source indices and preserve the smallest identifier on ties.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(edges) {
  // Scores can exceed 32 bits; keep ordinary exact Number values.
  const scores = new Array(edges.length).fill(0);
  for (let source = 0; source < edges.length; source += 1) scores[edges[source]] += source;
  let answer = 0;
  for (let node = 1; node < edges.length; node += 1) {
    if (scores[node] > scores[answer]) answer = node;
  }
  return answer;
}

const edgeScore = solve;
class Solution {
  edgeScore(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, edgeScore };
