"use strict";
// Hack2Hire 688e62068cf2da976a9c6903 (Find the K-th Highest Debit) over an INFERRED spec; qualification unknown.

function solve(loans, k) {
  const net = new Map();
  for (const [borrower, lender, amount] of loans) {
    const value = Number(amount);
    net.set(borrower, (net.get(borrower) || 0) + value);
    net.set(lender, (net.get(lender) || 0) - value);
  }
  const debtors = [];
  for (const [name, v] of net) if (v > 0) debtors.push([v, name]);
  debtors.sort((x, y) => y[0] - x[0] || (x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0));
  return k > debtors.length ? "" : debtors[k - 1][1];
}

function kthHighestDebtor(loans, k) { return solve(loans, k); }

module.exports = solve;
module.exports.kthHighestDebtor = kthHighestDebtor;
