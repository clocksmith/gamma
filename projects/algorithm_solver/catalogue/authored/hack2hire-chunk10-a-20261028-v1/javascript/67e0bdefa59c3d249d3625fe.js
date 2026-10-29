"use strict";
// Hack2Hire 67e0bdefa59c3d249d3625fe (Design Rate Limiter, variant 2 of 2) over an INFERRED spec; qualification unknown.

class Window {
  // accepted timestamps inside the window, as a queue with a moving head
  constructor() { this.items = []; this.head = 0; }
  get length() { return this.items.length - this.head; }
  expire(limit) {
    while (this.head < this.items.length && this.items[this.head] <= limit) this.head += 1;
    if (this.head > 1024 && this.head * 2 > this.items.length) { this.items = this.items.slice(this.head); this.head = 0; }
  }
}

class RateLimiter {
  constructor(limit, ttl) { this.limit = limit; this.ttl = ttl; this.windows = new Map(); } // client -> Window

  allowRequest(clientId, timestamp) {
    let w = this.windows.get(clientId);
    if (w === undefined) { w = new Window(); this.windows.set(clientId, w); }
    w.expire(timestamp - this.ttl);
    if (w.length < this.limit) { w.items.push(timestamp); return true; }
    return false;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RateLimiter" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new RateLimiter(...argumentLists[0]);
  const allowed = new Set(["allowRequest"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RateLimiter = RateLimiter;
