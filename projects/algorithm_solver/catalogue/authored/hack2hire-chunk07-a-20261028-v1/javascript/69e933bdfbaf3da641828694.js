"use strict";
// Hack2Hire 69e933bdfbaf3da641828694 (Maximize Portfolio Floor Value) over an INFERRED spec; qualification unknown.

function solve(values, costs, totalCost) {
  const order = values.map((_, i) => i).sort((a, b) => values[a] - values[b]);
  const vs = Float64Array.from(order, (i) => values[i]), cs = Float64Array.from(order, (i) => costs[i]);
  function affordable(target) {
    let spent = 0;
    for (let i = 0; i < vs.length; i++) {
      if (vs[i] >= target) break;
      spent += (target - vs[i]) * cs[i];  // each term <= 2 * 10^13 and spent stays <= totalCost + one term: exact
      if (spent > totalCost) return false;
    }
    return true;
  }
  let lo = vs[0], hi = vs[0] + totalCost;
  while (lo < hi) {
    const mid = Math.floor((lo + hi + 1) / 2);
    if (affordable(mid)) lo = mid; else hi = mid - 1;
  }
  return lo;
}

function maxPortfolioFloor(values, costs, totalCost) { return solve(values, costs, totalCost); }

module.exports = solve;
module.exports.maxPortfolioFloor = maxPortfolioFloor;
