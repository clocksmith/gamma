'use strict';

// 502. IPO (Hard).
// Specification: https://leetcode.com/problems/ipo/description/
function solve(k, w, profits, capital) {
  const projects = profits.map((profit, index) => [capital[index], profit]).sort((a, b) => a[0] - b[0]);
  let current = w; let index = 0; const affordable = [];
  for (let step = 0; step < k; step++) {
    while (index < projects.length && projects[index][0] <= current) { affordable.push(projects[index][1]); index++; }
    if (affordable.length === 0) break;
    affordable.sort((a, b) => b - a);
    current += affordable.shift();
  }
  return current;
}
const findMaximizedCapital = solve;
class Solution { findMaximizedCapital(k, w, profits, capital) { return solve(k, w, profits, capital); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximizedCapital };
