'use strict';

// 3733. Minimum Time to Complete All Deliveries.
// O(log(d1 + d2) + log(max r)) time and O(1) space; individual and union capacities characterize feasibility.
function solve(d, r) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  const common = r[0] / gcd(r[0], r[1]) * r[1];
  let left = 0;
  let right = 2 * (d[0] + d[1]);
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    const feasible = middle - Math.floor(middle / r[0]) >= d[0]
      && middle - Math.floor(middle / r[1]) >= d[1]
      && middle - Math.floor(middle / common) >= d[0] + d[1];
    if (feasible) right = middle;
    else left = middle + 1;
  }
  return left;
}

const minTime = solve;
class Solution {
  minTime(d, r) { return solve(d, r); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTime };
