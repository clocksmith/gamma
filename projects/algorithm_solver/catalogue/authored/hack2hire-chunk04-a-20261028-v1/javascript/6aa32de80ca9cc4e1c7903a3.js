"use strict";
// Hack2Hire 6aa32de80ca9cc4e1c7903a3 (Referral Credit Tracker, level 2) over an INFERRED spec; qualification unknown.

// Binary min-heap of numbers; key = -total * 32768 + id stays below 2**53 (total <= 4e10, id < 32768).
class NumberHeap {
  constructor() { this.a = []; }
  get size() { return this.a.length; }
  push(x) {
    const a = this.a;
    let i = a.length;
    a.push(x);
    while (i > 0) { const p = (i - 1) >> 1; if (a[p] <= x) break; a[i] = a[p]; i = p; }
    a[i] = x;
  }
  pop() {
    const a = this.a, top = a[0], x = a.pop(), n = a.length;
    if (n) {
      let i = 0;
      for (;;) {
        const l = 2 * i + 1;
        if (l >= n) break;
        const m = l + 1 < n && a[l + 1] < a[l] ? l + 1 : l;
        if (a[m] >= x) break;
        a[i] = a[m];
        i = m;
      }
      a[i] = x;
    }
    return top;
  }
}

class AccountCreditTracker {
  constructor() { this.totals = []; this.heap = new NumberHeap(); }

  _touch(account) { this.heap.push(-this.totals[account] * 32768 + account); }

  addAccount(credit) { this.totals.push(credit); this._touch(this.totals.length - 1); return this.totals.length - 1; }

  addAccountWithReferral(credit, referrerId) { this.totals[referrerId] += credit; this._touch(referrerId); return this.addAccount(credit); }

  getTotalCredit(accountId) { return this.totals[accountId]; }

  getTopAccounts(k) {
    const chosen = [], seen = new Set();
    while (this.heap.size && chosen.length < k) {
      const key = this.heap.pop(), account = ((key % 32768) + 32768) % 32768, total = (account - key) / 32768;
      if (total !== this.totals[account] || seen.has(account)) continue;
      seen.add(account);
      chosen.push(account);
    }
    for (const account of chosen) this.heap.push(-this.totals[account] * 32768 + account);
    return chosen;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "AccountCreditTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new AccountCreditTracker(...argumentLists[0]);
  const allowed = new Set(["addAccount", "addAccountWithReferral", "getTotalCredit", "getTopAccounts"]);
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
