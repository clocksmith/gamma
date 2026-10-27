'use strict';

// 601. Human Traffic of Stadium. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. stadium: id, visit_date (YYYY-MM-DD), people. Output: id, visit_date, people. Consecutiveness uses IDs, not calendar days.

function solve(stadium) {
  const good = new Set(stadium.filter(row => row.people >= 100).map(row => row.id));
  return stadium.filter(row => {
    const x = row.id;
    return good.has(x) && ((good.has(x - 2) && good.has(x - 1)) || (good.has(x - 1) && good.has(x + 1)) || (good.has(x + 1) && good.has(x + 2)));
  }).map(row => ({id: row.id, visit_date: row.visit_date, people: row.people}))
    .sort((a, b) => a.visit_date < b.visit_date ? -1 : a.visit_date > b.visit_date ? 1 : a.id - b.id);
}

const stadiumTraffic = solve;
class Solution {
  stadiumTraffic(stadium) { return solve(stadium); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stadiumTraffic };
