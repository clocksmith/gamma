'use strict';

// 3017. Count the Number of Houses at a Certain Distance II.
// For each left endpoint, distance values form at most three integer intervals; O(n) time and space. Counts include both directions.

function solve(n, x, y) {
  [x, y] = [Math.min(x, y), Math.max(x, y)];
  const changes = Array(n + 2).fill(0);
  function addInterval(left, right) { if (left <= right) { changes[left] += 1; changes[right + 1] -= 1; } }
  for (let first = 1; first <= n; first += 1) {
    const approach = Math.abs(first - x) + 1;
    if (approach + first >= y) { addInterval(1, n - first); continue; }
    const split = Math.floor((approach + y + first) / 2);
    addInterval(1, split - first);
    addInterval(approach + 1, approach + y - split - 1);
    addInterval(approach, approach + n - y);
  }
  const answer = [];
  let current = 0;
  for (let distance = 1; distance <= n; distance += 1) { current += changes[distance]; answer.push(2 * current); }
  return answer;
}

const countOfPairs = solve;
class Solution {
  countOfPairs(n, x, y) { return solve(n, x, y); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOfPairs };
