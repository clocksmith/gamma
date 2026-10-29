"use strict";
// Hack2Hire 6a629dc8190ed618c6e6b223 (Aggregate Recent Transactions) over an INFERRED spec; qualification unknown.

function cents(amount) {
  const [whole, fraction = ''] = amount.split('.');
  return BigInt(whole) * 100n + BigInt((fraction + '00').slice(0, 2));
}

function solve(transactions, currentTime) {
  const now = Number(currentTime), totals = new Map();
  for (const [amount, merchant, status, , start] of transactions) {
    const hours = Math.floor((now - Number(start)) / 3600);
    if (status === 'COMPLETED' && hours >= 0 && hours < 24) {
      if (!totals.has(merchant)) totals.set(merchant, [0n, 0]);
      const entry = totals.get(merchant);
      entry[0] += cents(amount);
      entry[1] += 1;
    }
  }
  return [...totals.keys()].sort().map((m) => {
    const [total, count] = totals.get(m);
    return [m, (total / 100n).toString() + '.' + (total % 100n).toString().padStart(2, '0'), count];
  });
}

function aggregateRecent(transactions, currentTime) { return solve(transactions, currentTime); }

module.exports = solve;
module.exports.aggregateRecent = aggregateRecent;
