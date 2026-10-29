"use strict";
// Hack2Hire 694b056e6e481a4b09cbc7e4 (Design a Moderator System, level 2) over an INFERRED spec; qualification unknown.

function upperBound(values, x) {
  let lo = 0, hi = values.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (values[mid] <= x) lo = mid + 1; else hi = mid; }
  return lo;
}

class ModSystem {
  constructor(logs) {
    this.rank = new Map();
    this.history = new Map();
    logs.forEach(([time, user, action], seq) => {
      const active = this.rank.has(user);
      if (action === "ADD" && !active) this.rank.set(user, seq);
      else if (action === "REMOVE" && active) this.rank.delete(user);
      else return;
      if (!this.history.has(user)) this.history.set(user, [[], []]);
      const entry = this.history.get(user);
      entry[0].push(time);
      entry[1].push(this.rank.has(user) ? this.rank.get(user) : -1);
    });
    this.order = [...this.rank.keys()].sort((a, b) => this.rank.get(a) - this.rank.get(b));
  }

  canRemove(actorId, targetId) {
    const rank = this.rank;
    return rank.has(actorId) && rank.has(targetId) && rank.get(actorId) < rank.get(targetId);
  }

  getModerators() { return this.order.slice(); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ModSystem" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ModSystem(...argumentLists[0]);
  const allowed = new Set(["canRemove", "getModerators"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ModSystem = ModSystem;
