'use strict';

// 1762. Buildings With an Ocean View (Medium).
// Specification: https://leetcode.com/problems/buildings-with-an-ocean-view/description/
function solve(heights) {
  const result = [];
  let tallest = 0;
  for (let i = heights.length - 1; i >= 0; i--) {
    if (heights[i] > tallest) { result.push(i); tallest = heights[i]; }
  }
  return result.reverse();
}
const findBuildings = solve;
class Solution { findBuildings(heights) { return solve(heights); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findBuildings };
