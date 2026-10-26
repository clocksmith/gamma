'use strict';

// 1772. Sort Features by Popularity: count each feature once per response and preserve original tie order.
// O(S + f log f) expected time and O(S + f) space for response text S and f features; inputs are read-only.
function solve(features, responses) {
  const counts = new Map(features.map(feature => [feature, 0]));
  for (const response of responses) {
    for (const word of new Set(response.split(' '))) {
      if (counts.has(word)) counts.set(word, counts.get(word) + 1);
    }
  }
  const order = Array.from({ length: features.length }, (_, index) => index);
  order.sort((left, right) => counts.get(features[right]) - counts.get(features[left]) || left - right);
  return order.map(index => features[index]);
}

const sortFeatures = solve;
class Solution {
  sortFeatures(features, responses) { return solve(features, responses); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortFeatures };
