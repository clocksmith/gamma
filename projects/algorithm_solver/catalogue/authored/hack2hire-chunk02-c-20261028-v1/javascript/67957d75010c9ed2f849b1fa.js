"use strict";
// Hack2Hire 67957d75010c9ed2f849b1fa (Account Balance Transfer, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class TransactionSystem {
  constructor(accounts, transactions) {
    this.order = accounts.map(a => a[0]);
    const balance = new Map(accounts.map(a => [a[0], a[1]]));
    this.history = new Map(accounts.map(a => [a[0], [[0], [a[1]]]])); // name -> [steps, balances]
    transactions.forEach(([source, target, percent], i) => {
      const moved = (balance.get(source) * percent - (balance.get(source) * percent) % 100) / 100;
      balance.set(source, balance.get(source) - moved);
      balance.set(target, balance.get(target) + moved);
      for (const name of [source, target]) {
        const [steps, values] = this.history.get(name);
        steps.push(i + 1);
        values.push(balance.get(name));
      }
    });
    this.balance = balance;
  }
  getBalance(name) { return this.balance.has(name) ? this.balance.get(name) : -1; }
  getBalances() { return this.order.map(name => [name, this.balance.get(name)]); }
  getBalanceAfter(name, k) {
    if (!this.history.has(name)) return -1;
    const [steps, values] = this.history.get(name);
    let lo = 0, hi = steps.length - 1; // last step <= k; steps[0] = 0 <= k
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (steps[mid] <= k) lo = mid; else hi = mid - 1;
    }
    return values[lo];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TransactionSystem") throw new Error("exact initial constructor required");
  const instance = new TransactionSystem(...argumentLists[0]);
  const allowed = new Set(["getBalance", "getBalances", "getBalanceAfter"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.TransactionSystem = TransactionSystem;
