"use strict";
// Hack2Hire 687c4741aa2b26b0b64b39ee (Design Banking System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class BankingSystem {
  constructor() {
    this.balance = new Map();
    this.outgoing = new Map();
    this.rankOut = []; this.rankIds = []; this.rankLabels = []; // sorted by outgoing desc, id asc; labels cached
  }
  rankIndex(out, id) { // first position not ordered before (out, id)
    let lo = 0, hi = this.rankIds.length;
    while (lo < hi) {
      const m = (lo + hi) >> 1;
      if (this.rankOut[m] > out || (this.rankOut[m] === out && this.rankIds[m] < id)) lo = m + 1; else hi = m;
    }
    return lo;
  }
  rankSet(account, old, now) {
    if (old !== null) { const i = this.rankIndex(old, account); this.rankOut.splice(i, 1); this.rankIds.splice(i, 1); this.rankLabels.splice(i, 1); }
    if (now !== null) { const i = this.rankIndex(now, account); this.rankOut.splice(i, 0, now); this.rankIds.splice(i, 0, account); this.rankLabels.splice(i, 0, account + "(" + now + ")"); }
  }
  createAccount(timestamp, accountId) {
    if (this.balance.has(accountId)) return false;
    this.balance.set(accountId, 0);
    this.outgoing.set(accountId, 0);
    this.rankSet(accountId, null, 0);
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
    this.rankSet(sourceAccountId, this.outgoing.get(sourceAccountId), this.outgoing.get(sourceAccountId) + amount);
    this.outgoing.set(sourceAccountId, this.outgoing.get(sourceAccountId) + amount);
    return this.balance.get(sourceAccountId);
  }
  topSpenders(timestamp, n) {
    return this.rankLabels.slice(0, n);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BankingSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new BankingSystem(...argumentLists[0]), allowed = new Set(["createAccount", "deposit", "transfer", "topSpenders"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.BankingSystem = BankingSystem;
