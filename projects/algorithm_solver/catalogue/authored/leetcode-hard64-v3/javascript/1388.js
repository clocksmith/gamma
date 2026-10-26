'use strict';

// 1388. Pizza With 3n Slices: two linear exact-cardinality independent-set DPs; O(n^2) time and O(n) space.

function solve(slices) {
  const required = Math.floor(slices.length / 3);
  function linear(start, end) {
    let previous = Array(required + 1).fill(-Infinity);
    previous[0] = 0;
    let beforePrevious = previous.slice();
    for (let index = start; index < end; index += 1) {
      const current = previous.slice();
      for (let count = 1; count <= required; count += 1) {
        current[count] = Math.max(previous[count], beforePrevious[count - 1] + slices[index]);
      }
      beforePrevious = previous;
      previous = current;
    }
    return previous[required];
  }
  return Math.max(linear(0, slices.length - 1), linear(1, slices.length));
}

const maxSizeSlices = solve;
class Solution {
  maxSizeSlices(slices) { return solve(slices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSizeSlices };
