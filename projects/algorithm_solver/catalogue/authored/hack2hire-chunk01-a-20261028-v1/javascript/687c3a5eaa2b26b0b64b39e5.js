"use strict";
// Hack2Hire 687c3a5eaa2b26b0b64b39e5 (Design Banking System, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class BankingSystem {
  constructor() {
    this.balance = new Map();
  }
  createAccount(timestamp, accountId) {
    if (this.balance.has(accountId)) return false;
    this.balance.set(accountId, 0);
    return true;
  }
  deposit(timestamp, accountId, amount) {
    if (!this.balance.has(accountId)) return -1;
    this.balance.set(accountId, this.balance.get(accountId) + amount);
    return this.balance.get(accountId);
  }
  transfer(timestamp, sourceAccountId, targetAccountId, amount) {
    if (sourceAccountId === targetAccountId || !this.balance.has(sourceAccountId) || !this.balance.has(targetAccountId) ||
        this.balance.get(sourceAccountId) < amount) return -1;
    this.balance.set(sourceAccountId, this.balance.get(sourceAccountId) - amount);
    this.balance.set(targetAccountId, this.balance.get(targetAccountId) + amount);
    return this.balance.get(sourceAccountId);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BankingSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new BankingSystem(...argumentLists[0]), allowed = new Set(["createAccount", "deposit", "transfer"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.BankingSystem = BankingSystem;
