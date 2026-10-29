"use strict";
// Hack2Hire 67957d70010c9ed2f849b1f9 (Account Balance Transfer, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class TransactionSystem {
  constructor(accounts, transactions) {
    this.order = accounts.map(a => a[0]);
    const balance = new Map(accounts.map(a => [a[0], a[1]]));
    for (const [source, target, percent] of transactions) {
      const moved = (balance.get(source) * percent - (balance.get(source) * percent) % 100) / 100;
      balance.set(source, balance.get(source) - moved);
      balance.set(target, balance.get(target) + moved);
    }
    this.balance = balance;
  }
  getBalance(name) { return this.balance.has(name) ? this.balance.get(name) : -1; }
  getBalances() { return this.order.map(name => [name, this.balance.get(name)]); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TransactionSystem") throw new Error("exact initial constructor required");
  const instance = new TransactionSystem(...argumentLists[0]);
  const allowed = new Set(["getBalance", "getBalances"]);
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
