"use strict";
// Hack2Hire 6a7a3b72d713d873ca7aaf62 (Apply Domain Request Limits) over an INFERRED spec; qualification unknown.

class DomainRateLimiter {
  constructor(maxRequests, windowSize) {
    this.limit = maxRequests; this.window = windowSize; this.clock = 0;
    this.accepted = new Map(); // domain -> {times, head}: a queue with a moving head
  }

  allowRequest(domain) {
    this.clock += 1;
    let q = this.accepted.get(domain);
    if (q === undefined) { q = {times: [], head: 0}; this.accepted.set(domain, q); }
    const oldest = this.clock - this.window;
    while (q.head < q.times.length && q.times[q.head] <= oldest) q.head += 1;
    if (q.head > 1024 && q.head * 2 > q.times.length) { q.times = q.times.slice(q.head); q.head = 0; }
    if (q.times.length - q.head < this.limit) { q.times.push(this.clock); return true; }
    return false;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DomainRateLimiter" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new DomainRateLimiter(...argumentLists[0]);
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
module.exports.DomainRateLimiter = DomainRateLimiter;
