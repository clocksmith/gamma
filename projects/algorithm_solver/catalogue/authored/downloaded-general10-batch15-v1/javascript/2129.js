'use strict';

// 2129. Capitalize the Title (Easy).
// Specification: https://leetcode.com/problems/capitalize-the-title/description/
function solve(title) {
  return title.split(' ').map((word) => {
    const lower = word.toLowerCase();
    if (lower.length <= 2) return lower;
    return lower[0].toUpperCase() + lower.slice(1);
  }).join(' ');
}
const capitalizeTitle = solve;
class Solution { capitalizeTitle(title) { return solve(title); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, capitalizeTitle };
