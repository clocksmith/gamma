'use strict';

// 3694. Distinct Points Reachable After Substring Removal.
// O(n) time and O(n) space; unique removed displacements correspond bijectively to final positions.
function solve(s, k) {
  const direction = { U: [0, 1], D: [0, -1], L: [-1, 0], R: [1, 0] };
  let horizontal = 0;
  let vertical = 0;
  for (let index = 0; index < k; index += 1) {
    const [dx, dy] = direction[s[index]];
    horizontal += dx;
    vertical += dy;
  }
  const seen = new Set([`${horizontal},${vertical}`]);
  for (let index = k; index < s.length; index += 1) {
    const removed = direction[s[index - k]];
    const added = direction[s[index]];
    horizontal += added[0] - removed[0];
    vertical += added[1] - removed[1];
    seen.add(`${horizontal},${vertical}`);
  }
  return seen.size;
}

const distinctPoints = solve;
class Solution {
  distinctPoints(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctPoints };
