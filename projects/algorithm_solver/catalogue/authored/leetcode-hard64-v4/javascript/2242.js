'use strict';

// 2242. Maximum Score of a Node Sequence. Three best neighbors at each end of the middle edge; O(V+E) time and O(V) auxiliary space. Inputs are preserved.

function solve(scores, edges) {
  const neighbors = Array.from({ length: scores.length }, () => []);
  function addNeighbor(source, target) {
    neighbors[source].push(target);
    neighbors[source].sort((a, b) => scores[b] - scores[a]);
    if (neighbors[source].length > 3) neighbors[source].pop();
  }
  for (const [first, second] of edges) {
    addNeighbor(first, second);
    addNeighbor(second, first);
  }
  let answer = -1;
  for (const [first, second] of edges) {
    for (const left of neighbors[first]) {
      if (left === second) continue;
      for (const right of neighbors[second]) {
        if (right !== first && right !== left) {
          answer = Math.max(answer, scores[left] + scores[first] + scores[second] + scores[right]);
        }
      }
    }
  }
  return answer;
}

const maximumScore = solve;
class Solution {
  maximumScore(scores, edges) { return solve(scores, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
