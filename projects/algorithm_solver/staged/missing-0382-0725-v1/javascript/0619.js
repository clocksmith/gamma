'use strict';

// 619. Biggest Single Number. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. my_numbers: num, duplicates allowed. Output: num; no single number yields NULL.

function solve(my_numbers) {
  const counts = new Map();
  for (const row of my_numbers) counts.set(row.num, (counts.get(row.num) || 0) + 1);
  let best = null;
  for (const [value, count] of counts) if (value != null && count === 1 && (best === null || value > best)) best = value;
  return [{num: best}];
}

const biggestSingleNumber = solve;
class Solution {
  biggestSingleNumber(my_numbers) { return solve(my_numbers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, biggestSingleNumber };
