'use strict';

// 2141. Maximum Running Time of N Computers. Binary search using clipped total energy; O(m log(sum(batteries))) time, O(1) auxiliary space. Inputs are preserved.

function solve(n, batteries) {
  let total = 0;
  for (const capacity of batteries) total += capacity;
  let left = 0;
  let right = Math.floor(total / n);
  while (left < right) {
    const duration = Math.floor((left + right + 1) / 2);
    let available = 0;
    for (const capacity of batteries) available += Math.min(capacity, duration);
    if (available >= n * duration) left = duration;
    else right = duration - 1;
  }
  return left;
}

const maxRunTime = solve;
class Solution {
  maxRunTime(n, batteries) { return solve(n, batteries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRunTime };
