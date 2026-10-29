"use strict";
// Hack2Hire 687c4e56024483ac76db8c9b (Design Banking System, variant 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const DAY_MS = 86400000;
class BankingSystem {
  constructor() {
    this.balance = new Map();
    this.outgoing = new Map();
    this.rankOut = []; this.rankIds = []; this.rankLabels = []; // sorted by outgoing desc, id asc; labels cached
    this.payments = new Map(); // payment id -> [owner, amount, status]
    this.owned = new Map(); // account -> payment ids it owns
    this.cashbacks = []; // [due, payment]; due times increase with timestamps
    this.cashbackHead = 0;
    this.paymentCount = 0;
  }
  settle(timestamp) {
    while (this.cashbackHead < this.cashbacks.length && this.cashbacks[this.cashbackHead][0] <= timestamp) {
      const [due, payment] = this.cashbacks[this.cashbackHead++], record = this.payments.get(payment);
      this.balance.set(record[0], this.balance.get(record[0]) + Math.floor(record[1] * 2 / 100));
      record[2] = "CASHBACK_RECEIVED";
    }
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
    this.settle(timestamp);
    if (this.balance.has(accountId)) return false;
    this.balance.set(accountId, 0);
    this.outgoing.set(accountId, 0);
    this.rankSet(accountId, null, 0);
    this.owned.set(accountId, []);
    return true;
  }
  deposit(timestamp, accountId, amount) {
    this.settle(timestamp);
    if (!this.balance.has(accountId)) return -1;
    this.balance.set(accountId, this.balance.get(accountId) + amount);
    return this.balance.get(accountId);
  }
  transfer(timestamp, sourceAccountId, targetAccountId, amount) {
    this.settle(timestamp);
    if (sourceAccountId === targetAccountId || !this.balance.has(sourceAccountId) || !this.balance.has(targetAccountId) ||
        this.balance.get(sourceAccountId) < amount) return -1;
    this.balance.set(sourceAccountId, this.balance.get(sourceAccountId) - amount);
    this.balance.set(targetAccountId, this.balance.get(targetAccountId) + amount);
    this.rankSet(sourceAccountId, this.outgoing.get(sourceAccountId), this.outgoing.get(sourceAccountId) + amount);
    this.outgoing.set(sourceAccountId, this.outgoing.get(sourceAccountId) + amount);
    return this.balance.get(sourceAccountId);
  }
  topSpenders(timestamp, n) {
    this.settle(timestamp);
    return this.rankLabels.slice(0, n);
  }
  pay(timestamp, accountId, amount) {
    this.settle(timestamp);
    if (!this.balance.has(accountId) || this.balance.get(accountId) < amount) return null;
    this.balance.set(accountId, this.balance.get(accountId) - amount);
    this.rankSet(accountId, this.outgoing.get(accountId), this.outgoing.get(accountId) + amount);
    this.outgoing.set(accountId, this.outgoing.get(accountId) + amount);
    const payment = "payment" + (++this.paymentCount);
    this.payments.set(payment, [accountId, amount, "IN_PROGRESS"]);
    this.owned.get(accountId).push(payment);
    this.cashbacks.push([timestamp + DAY_MS, payment]);
    return payment;
  }
  getPaymentStatus(timestamp, accountId, payment) {
    this.settle(timestamp);
    const record = this.payments.get(payment);
    if (!this.balance.has(accountId) || record === undefined || record[0] !== accountId) return null;
    return record[2];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BankingSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new BankingSystem(...argumentLists[0]), allowed = new Set(["createAccount", "deposit", "transfer", "topSpenders", "pay", "getPaymentStatus"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.BankingSystem = BankingSystem;
