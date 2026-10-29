"use strict";
// Hack2Hire 69bdad5c1cbff60a929beab2 (Maximum Profit Query Selection) over an INFERRED spec; qualification unknown.

function solve(executionTime, profit, k) {
  let best = 0, index = -1;
  for (let i = 0; i < executionTime.length; i++) {
    const value = Math.floor(k / executionTime[i]) * profit[i];
    if (value > best) { best = value; index = i; }
  }
  return [best, index];
}

function maxProfitQuery(executionTime, profit, k) { return solve(executionTime, profit, k); }

module.exports = solve;
module.exports.maxProfitQuery = maxProfitQuery;
