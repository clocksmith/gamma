'use strict';

// 2109. Adding Spaces to a String: join untouched source slices at the specified insertion positions.
// O(n + m) time and O(n + m) output-construction space; inputs are read-only.
function solve(s, spaces) {
  const pieces = [];
  let previous = 0;
  for (const position of spaces) {
    pieces.push(s.slice(previous, position));
    previous = position;
  }
  pieces.push(s.slice(previous));
  return pieces.join(' ');
}

const addSpaces = solve;
class Solution {
  addSpaces(s, spaces) { return solve(s, spaces); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addSpaces };
