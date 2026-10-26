'use strict';

// 2251. Number of Flowers in Full Bloom. Count starts at or before a visit minus ends strictly before it; O((F+P) log F) time, O(F+P) space. Inputs are preserved.

function solve(flowers, people) {
  const starts = flowers.map(interval => interval[0]).sort((a, b) => a - b);
  const ends = flowers.map(interval => interval[1]).sort((a, b) => a - b);
  function boundary(values, instant, inclusive) {
    let left = 0;
    let right = values.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (values[middle] < instant || (inclusive && values[middle] === instant)) left = middle + 1;
      else right = middle;
    }
    return left;
  }
  return people.map(instant => boundary(starts, instant, true) - boundary(ends, instant, false));
}

const fullBloomFlowers = solve;
class Solution {
  fullBloomFlowers(flowers, people) { return solve(flowers, people); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fullBloomFlowers };
