"use strict";
// Hack2Hire 69117148869dd6a56c434054 (GPU Credits); INFERRED spec; qualification unknown.
class CreditSystem {
  constructor() { this.grants = new Map(); }
  addCredit(creditId, amount, startTime, endTime) { this.grants.set(creditId, [amount, startTime, endTime, null]); }
  revokeCredit(creditId, timestamp) {
    const grant = this.grants.get(creditId);
    if (grant === undefined || grant[3] !== null) return false;
    grant[3] = timestamp;
    return true;
  }
  getBalance(timestamp) {
    let total = 0;
    for (const [amount, start, end, revoked] of this.grants.values()) {
      if (start <= timestamp && timestamp <= end && (revoked === null || timestamp < revoked)) total += amount;
    }
    return total;
  }
}
function solve(operations, args) {
  const system = new CreditSystem(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = system[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.CreditSystem = CreditSystem;
