'use strict';

// 2528. Maximize the Minimum Powered City. Binary search the minimum power with rightmost greedy placements; O(n log(k+2)) time and O(n) space. Inputs are preserved.

function solve(stations, r, k) {
  const size = stations.length;
  const prefix = Array(size + 1).fill(0);
  for (let index = 0; index < size; index += 1) prefix[index + 1] = prefix[index] + stations[index];
  const power = Array(size);
  let low = Infinity;
  for (let index = 0; index < size; index += 1) {
    power[index] = prefix[Math.min(size, index + r + 1)] - prefix[Math.max(0, index - r)];
    low = Math.min(low, power[index]);
  }
  function feasible(target) {
    const changes = Array(size + 1).fill(0);
    let active = 0;
    let used = 0;
    for (let index = 0; index < size; index += 1) {
      active += changes[index];
      const missing = target - power[index] - active;
      if (missing <= 0) continue;
      used += missing;
      if (used > k) return false;
      active += missing;
      changes[Math.min(size, index + 2 * r + 1)] -= missing;
    }
    return true;
  }
  let high = low + k;
  while (low < high) {
    const middle = Math.floor((low + high + 1) / 2);
    if (feasible(middle)) low = middle;
    else high = middle - 1;
  }
  return low;
}

const maxPower = solve;
class Solution {
  maxPower(stations, r, k) { return solve(stations, r, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPower };
