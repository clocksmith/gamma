"use strict";
// Hack2Hire 6a7231c748af2ae18e995d8b (Group Loans by Top-Level Company, v2); INFERRED from title only; qualification unknown.
function cmpStr(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function solve(parents, loans) {
  const parent = new Map(parents), root = new Map(), totals = new Map();
  const find = company => {
    const path = [];
    while (parent.has(company) && !root.has(company)) { path.push(company); company = parent.get(company); }
    const top = root.has(company) ? root.get(company) : company;
    for (const c of path) root.set(c, top);
    return top;
  };
  for (const [, company, amount] of loans) { const top = find(company); totals.set(top, (totals.get(top) || 0) + amount); }
  return [...totals.keys()].sort((a, b) => totals.get(b) - totals.get(a) || cmpStr(a, b)).map(top => [top, totals.get(top)]);
}
function totalLoansByTopCompany(parents, loans) { return solve(parents, loans); }
module.exports = solve;
module.exports.totalLoansByTopCompany = totalLoansByTopCompany;
