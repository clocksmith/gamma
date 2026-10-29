// Original hack2hire:679039a5dda371fa278429f4; inferred public-preview contract; qualification unknown.
"use strict";
class CryptoTradingSystem {
  constructor() { this.orders = new Map(); }
  place(id, currency, amount, timestamp, type) {
    if (this.orders.has(id)) return false;
    this.orders.set(id, {id, currency, amount, timestamp, type, state:'live'}); return true;
  }
  _transition(id, allowed, target) {
    const row = this.orders.get(id);
    if (!row || !allowed.includes(row.state)) return false;
    row.state = target; return true;
  }
  pause(id) { return this._transition(id, ['live'], 'paused'); }
  resume(id) { return this._transition(id, ['paused'], 'live'); }
  cancel(id) { return this._transition(id, ['live','paused'], 'canceled'); }
  complete(id) { return this._transition(id, ['live'], 'completed'); }
  listLive(currency) {
    const compareId = (left, right) => {
      const a = Array.from(left, ch => ch.codePointAt(0)), b = Array.from(right, ch => ch.codePointAt(0));
      for (let i = 0; i < Math.min(a.length,b.length); i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
      return a.length-b.length;
    };
    return [...this.orders.values()].filter(row => row.state === 'live' && (currency === null || row.currency === currency))
      .sort((a,b) => a.timestamp-b.timestamp || compareId(a.id,b.id)).map(row => ({...row}));
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "CryptoTradingSystem") throw new Error("exact constructor trace required");
  const instance = new CryptoTradingSystem(...argumentLists[0]), result = [null], allowed = new Set(["place", "pause", "resume", "cancel", "complete", "listLive"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.CryptoTradingSystem = CryptoTradingSystem;
