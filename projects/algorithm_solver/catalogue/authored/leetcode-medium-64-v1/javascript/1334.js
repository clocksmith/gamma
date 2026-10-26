'use strict';

// 1334. Find the City With the Smallest Number of Neighbors at a Threshold Distance: compute all-pairs distances and resolve count ties toward the larger city.
// O(n^3) time and O(n^2) auxiliary space; inputs are read-only.
function solve(n, edges, distanceThreshold) {
  const distances = Array.from({ length: n }, () => new Array(n).fill(Infinity));
  for (let city = 0; city < n; city += 1) distances[city][city] = 0;
  for (const [left, right, weight] of edges) {
    distances[left][right] = Math.min(distances[left][right], weight);
    distances[right][left] = Math.min(distances[right][left], weight);
  }
  for (let middle = 0; middle < n; middle += 1) {
    for (let left = 0; left < n; left += 1) {
      const first = distances[left][middle];
      if (first === Infinity) continue;
      for (let right = 0; right < n; right += 1) {
        distances[left][right] = Math.min(distances[left][right], first + distances[middle][right]);
      }
    }
  }
  let answer = -1;
  let fewest = n;
  for (let city = 0; city < n; city += 1) {
    let count = 0;
    for (let other = 0; other < n; other += 1) {
      if (other !== city && distances[city][other] <= distanceThreshold) count += 1;
    }
    if (count <= fewest) { answer = city; fewest = count; }
  }
  return answer;
}

const findTheCity = solve;
class Solution {
  findTheCity(n, edges, distanceThreshold) { return solve(n, edges, distanceThreshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheCity };
