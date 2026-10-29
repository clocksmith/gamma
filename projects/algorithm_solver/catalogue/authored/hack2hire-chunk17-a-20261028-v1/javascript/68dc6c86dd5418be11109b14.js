"use strict";
// Hack2Hire 68dc6c86dd5418be11109b14 (Stock Trade Ranking System) over an INFERRED spec; qualification unknown.

class StockTracker {
  constructor() {
    this.totals = new Map();
    this.ranking = [];
    this.dirty = false;
  }

  recordTrade(stockName, quantity) {
    this.totals.set(stockName, (this.totals.get(stockName) || 0) + quantity);
    this.dirty = true;
  }

  getRankedStocks() {
    if (this.dirty) {
      const totals = this.totals;
      this.ranking = Array.from(totals.keys()).sort((a, b) => (totals.get(b) - totals.get(a)) || (a < b ? -1 : a > b ? 1 : 0));
      this.dirty = false;
    }
    return this.ranking.slice();
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "StockTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new StockTracker(...argumentLists[0]);
  const allowed = new Set(["recordTrade", "getRankedStocks"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.StockTracker = StockTracker;
