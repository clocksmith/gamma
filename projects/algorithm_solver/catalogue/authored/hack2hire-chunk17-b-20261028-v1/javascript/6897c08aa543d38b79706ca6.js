"use strict";
// Hack2Hire 6897c08aa543d38b79706ca6 (Cross-Day User Trust Scoring) over an INFERRED spec; qualification unknown.

class PurchaseAnalyzer {
  constructor(logsDay1, logsDay2) {
    const days = new Map();
    const types = new Map();
    [[1, logsDay1], [2, logsDay2]].forEach(([bit, logs]) => {
      for (const row of logs) {
        const user = row[1];
        days.set(user, (days.get(user) || 0) | bit);
        let kinds = types.get(user);
        if (kinds === undefined) { kinds = new Set(); types.set(user, kinds); }
        kinds.add(row[2]);
      }
    });
    this.users = [];
    for (const [user, mask] of days) if (mask === 3 && types.get(user).size >= 2) this.users.push(user);
    this.users.sort();
  }

  crossDayDiverseUsers() {
    return this.users.slice();
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PurchaseAnalyzer" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new PurchaseAnalyzer(...argumentLists[0]);
  const allowed = new Set(["crossDayDiverseUsers"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PurchaseAnalyzer = PurchaseAnalyzer;
