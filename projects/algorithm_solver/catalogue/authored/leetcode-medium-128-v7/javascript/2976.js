'use strict';

// 2976. Minimum Cost to Convert String I: compute all-pairs character conversion costs before summing corresponding positions.
// O(26^3 + n + e) time and O(26^2) auxiliary space; inputs are read-only.
function solve(source, target, original, changed, cost) {
  const distance = Array.from({ length: 26 }, () => new Array(26).fill(Infinity));
  for (let code = 0; code < 26; code += 1) distance[code][code] = 0;
  for (let index = 0; index < original.length; index += 1) {
    const left = original[index].charCodeAt(0) - 97;
    const right = changed[index].charCodeAt(0) - 97;
    distance[left][right] = Math.min(distance[left][right], cost[index]);
  }
  for (let middle = 0; middle < 26; middle += 1) {
    for (let left = 0; left < 26; left += 1) {
      if (distance[left][middle] === Infinity) continue;
      for (let right = 0; right < 26; right += 1) {
        distance[left][right] = Math.min(distance[left][right], distance[left][middle] + distance[middle][right]);
      }
    }
  }
  let total = 0;
  for (let index = 0; index < source.length; index += 1) {
    const price = distance[source.charCodeAt(index) - 97][target.charCodeAt(index) - 97];
    if (price === Infinity) return -1;
    total += price;
  }
  return total;
}

const minimumCost = solve;
class Solution {
  minimumCost(source, target, original, changed, cost) { return solve(source, target, original, changed, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
