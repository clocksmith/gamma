'use strict';

// 1494. Parallel Courses II: completed-course masks and feasible semester subsets; O(3^n+n*2^n) time and O(2^n) space.

function solve(n, relations, k) {
  const prerequisites = Array(n).fill(0);
  for (const [before, after] of relations) prerequisites[after - 1] |= 1 << (before - 1);
  const full = (1 << n) - 1;
  const best = Array(full + 1).fill(n + 1);
  best[0] = 0;
  function countBits(value) {
    let count = 0;
    for (; value !== 0; value &= value - 1) count += 1;
    return count;
  }
  for (let completed = 0; completed < full; completed += 1) {
    if (best[completed] > n) continue;
    let available = 0;
    for (let course = 0; course < n; course += 1) {
      if ((completed & (1 << course)) === 0 && (prerequisites[course] & completed) === prerequisites[course]) available |= 1 << course;
    }
    if (countBits(available) <= k) {
      const following = completed | available;
      best[following] = Math.min(best[following], best[completed] + 1);
    } else {
      for (let subset = available; subset !== 0; subset = (subset - 1) & available) {
        if (countBits(subset) === k) {
          const following = completed | subset;
          best[following] = Math.min(best[following], best[completed] + 1);
        }
      }
    }
  }
  return best[full];
}

const minNumberOfSemesters = solve;
class Solution {
  minNumberOfSemesters(n, relations, k) { return solve(n, relations, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumberOfSemesters };
