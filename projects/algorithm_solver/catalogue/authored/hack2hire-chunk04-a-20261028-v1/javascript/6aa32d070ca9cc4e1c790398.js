"use strict";
// Hack2Hire 6aa32d070ca9cc4e1c790398 (Referral Credit Tracker, level 1) over an INFERRED spec; qualification unknown.

class AccountCreditTracker {
  constructor() { this.totals = []; }

  _touch(account) {}

  addAccount(credit) { this.totals.push(credit); this._touch(this.totals.length - 1); return this.totals.length - 1; }

  addAccountWithReferral(credit, referrerId) { this.totals[referrerId] += credit; this._touch(referrerId); return this.addAccount(credit); }

  getTotalCredit(accountId) { return this.totals[accountId]; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "AccountCreditTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new AccountCreditTracker(...argumentLists[0]);
  const allowed = new Set(["addAccount", "addAccountWithReferral", "getTotalCredit"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.AccountCreditTracker = AccountCreditTracker;
