'use strict';

// 3206. Alternating Groups I (Easy).
// Specification: https://leetcode.com/problems/alternating-groups-i/description/
// O(n) time, O(1) auxiliary space; count circular groups of exactly three tiles.
function solve(colors) {
  const size = colors.length;
  let groups = 0;
  for (let center = 0; center < size; center++) {
    const previous = colors[(center + size - 1) % size];
    const next = colors[(center + 1) % size];
    if (colors[center] !== previous && colors[center] !== next) groups++;
  }
  return groups;
}

const numberOfAlternatingGroups = solve;
class Solution {
  numberOfAlternatingGroups(colors) { return solve(colors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfAlternatingGroups };
