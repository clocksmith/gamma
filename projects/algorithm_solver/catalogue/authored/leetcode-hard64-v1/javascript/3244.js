'use strict';

// 3244. Shortest Distance After Road Addition Queries II: permanently bypass vertices under the noncrossing-query contract.
// O(n + q) time and O(n + q) space. Inputs are preserved.
function solve(n, queries) {
  const following = Int32Array.from({ length: n }, (_, index) => index + 1);
  let distance = n - 1;
  const answer = [];
  for (const [left, right] of queries) {
    if (following[left] !== -1 && following[left] < right) {
      let node = following[left];
      while (node < right) {
        const successor = following[node];
        following[node] = -1;
        distance -= 1;
        node = successor;
      }
      following[left] = right;
    }
    answer.push(distance);
  }
  return answer;
}

const shortestDistanceAfterQueries = solve;
class Solution {
  shortestDistanceAfterQueries(n, queries) { return solve(n, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistanceAfterQueries };
