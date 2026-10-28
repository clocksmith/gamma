'use strict';

// 957. Prison Cells After N Days (Medium).
// Specification: https://leetcode.com/problems/prison-cells-after-n-days/description/
function solve(cells, n) {
  const seen = new Map();
  let current = cells.slice();
  let day = 0;
  while (day < n) {
    const key = current.join(',');
    if (seen.has(key)) {
      const cycle = day - seen.get(key);
      const remaining = (n - day) % cycle;
      for (let i = 0; i < remaining; i++) current = nextDay(current);
      return current;
    }
    seen.set(key, day);
    current = nextDay(current);
    day++;
  }
  return current;
}
function nextDay(cells) {
  const next = new Array(8).fill(0);
  for (let i = 1; i < 7; i++) next[i] = cells[i - 1] === cells[i + 1] ? 1 : 0;
  return next;
}
const prisonAfterNDays = solve;
class Solution { prisonAfterNDays(cells, n) { return solve(cells, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, prisonAfterNDays };
