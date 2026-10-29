"use strict";
// Hack2Hire 69810d3cf8f2604d5eecfff4 (Account Balance Processor, level 1) over an INFERRED spec; qualification unknown.

const LEVEL = 1;

function solve(logs) {
  let records = logs.map((line) => line.split(','));
  if (LEVEL >= 2) {
    const seen = new Set();
    records = records.filter((record) => { if (seen.has(record[0])) return false; seen.add(record[0]); return true; });
  }
  const balance = new Map();
  for (const record of records) if (!balance.has(record[1])) balance.set(record[1], 0);
  const rejected = [];
  if (LEVEL === 3) records = records.slice().sort((x, y) => Number(x[3]) - Number(y[3]));
  for (const [txn, account, amount] of records) {
    const value = Number(amount);
    if (LEVEL === 3 && balance.get(account) + value < 0) { rejected.push(txn); continue; }
    balance.set(account, balance.get(account) + value + 0);
  }
  const rows = [...balance.keys()].sort().map((account) => [account, balance.get(account) + 0]);
  return LEVEL === 3 ? [rows, rejected] : rows;
}

function processLogs(logs) { return solve(logs); }

module.exports = solve;
module.exports.processLogs = processLogs;
