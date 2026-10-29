"use strict";
// Hack2Hire 694b08dc6e481a4b09cbc807 (Design a Moderator System, level 3) over an INFERRED spec; qualification unknown.

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

  rankAt(user, time) {
    const entry = this.history.get(user);
    if (entry === undefined) return -1;
    const index = upperBound(entry[0], time);
    return index ? entry[1][index - 1] : -1;
  }

  canRemoveAt(time, actorId, targetId) {
    const a = this.rankAt(actorId, time), b = this.rankAt(targetId, time);
    return a >= 0 && b >= 0 && a < b;
  }

  getModeratorsAt(time) {
    const ranked = [];
    for (const user of this.history.keys()) {
      const r = this.rankAt(user, time);
      if (r >= 0) ranked.push([r, user]);
    }
    ranked.sort((x, y) => x[0] - y[0]);
    return ranked.map((x) => x[1]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ModSystem" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ModSystem(...argumentLists[0]);
  const allowed = new Set(["canRemove", "getModerators", "canRemoveAt", "getModeratorsAt"]);
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
