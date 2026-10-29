"use strict";
// Hack2Hire 6a611985c16dcdf8ba4ff8a2 (Group Loans by Top-Level Company, v1); INFERRED from title only; qualification unknown.
function cmpStr(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function rootFinder(parents) {
  const parent = new Map(parents), root = new Map();
  return company => {
    const path = [];
    while (parent.has(company) && !root.has(company)) { path.push(company); company = parent.get(company); }
    const top = root.has(company) ? root.get(company) : company;
    for (const c of path) root.set(c, top);
    return top;
  };
}
function solve(parents, loans) {
  const find = rootFinder(parents), groups = new Map();
  for (const [loanId, company] of loans) {
    const top = find(company);
    if (!groups.has(top)) groups.set(top, []);
    groups.get(top).push(loanId);
  }
  return [...groups.keys()].sort(cmpStr).map(top => [top, groups.get(top).slice().sort(cmpStr)]);
}
function groupLoansByTopCompany(parents, loans) { return solve(parents, loans); }
module.exports = solve;
module.exports.groupLoansByTopCompany = groupLoansByTopCompany;
