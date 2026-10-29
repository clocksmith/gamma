"use strict";
// Hack2Hire 6a516506665efda9311f618d (Bank Transaction Mining) over an INFERRED spec; qualification unknown.

function solve(accounts, transactions) {
  const index = new Map(accounts.map(([number], i) => [number, i]));
  const balance = accounts.map(([, b]) => Number(b));
  for (const [, source, target, amount] of transactions) {
    const s = index.get(source), t = index.get(target), value = Number(amount);
    if (s !== undefined && t !== undefined && s !== t && balance[s] >= value) { balance[s] -= value; balance[t] += value; }
  }
  const order = accounts.map((_, i) => i);
  order.sort((x, y) => balance[y] - balance[x] || (accounts[x][0] < accounts[y][0] ? -1 : accounts[x][0] > accounts[y][0] ? 1 : 0));
  return order.map((i) => [accounts[i][0], String(balance[i])]);
}

function mineTransactions(accounts, transactions) { return solve(accounts, transactions); }

module.exports = solve;
module.exports.mineTransactions = mineTransactions;
