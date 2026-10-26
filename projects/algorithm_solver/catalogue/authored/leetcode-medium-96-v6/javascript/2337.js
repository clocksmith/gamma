'use strict';

// 2337. Move Pieces to Obtain a String: match piece order while checking each piece can move only in its permitted direction.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(start, target) {
  if (start.length !== target.length) return false;
  let left = 0;
  let right = 0;
  const size = start.length;
  while (true) {
    while (left < size && start[left] === '_') left += 1;
    while (right < size && target[right] === '_') right += 1;
    if (left === size || right === size) return left === size && right === size;
    if (start[left] !== target[right]) return false;
    if (start[left] === 'L' && left < right) return false;
    if (start[left] === 'R' && left > right) return false;
    left += 1;
    right += 1;
  }
}

const canChange = solve;
class Solution {
  canChange(start, target) { return solve(start, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canChange };
