'use strict';

// 2211. Count Collisions on a Road: discard cars escaping outward and count every moving car left inside.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(directions) {
  let left = 0;
  let right = directions.length - 1;
  while (left <= right && directions[left] === 'L') left += 1;
  while (left <= right && directions[right] === 'R') right -= 1;
  let collisions = 0;
  for (let index = left; index <= right; index += 1) {
    if (directions[index] !== 'S') collisions += 1;
  }
  return collisions;
}

const countCollisions = solve;
class Solution {
  countCollisions(directions) { return solve(directions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCollisions };
