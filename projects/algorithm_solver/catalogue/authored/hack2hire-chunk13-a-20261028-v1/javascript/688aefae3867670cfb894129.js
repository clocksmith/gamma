"use strict";
// Hack2Hire 688aefae3867670cfb894129 (Oldest One-Time Visitor) over an INFERRED spec; qualification unknown.

class VisitorTracker {
  constructor() {
    this.count = new Map();
    this.order = []; // usernames in order of their first login
    this.head = 0;
  }

  login(username) {
    const seen = this.count.get(username) || 0;
    if (seen === 0) this.order.push(username);
    this.count.set(username, seen + 1);
  }

  getOldestOneTimeVisitor() {
    while (this.head < this.order.length && this.count.get(this.order[this.head]) > 1) this.head++; // repeat visitors never return
    return this.head < this.order.length ? this.order[this.head] : "";
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "VisitorTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new VisitorTracker(...argumentLists[0]);
  const allowed = new Set(["login", "getOldestOneTimeVisitor"]);
  const voids = new Set(["login"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(voids.has(operationNames[i]) ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.VisitorTracker = VisitorTracker;
