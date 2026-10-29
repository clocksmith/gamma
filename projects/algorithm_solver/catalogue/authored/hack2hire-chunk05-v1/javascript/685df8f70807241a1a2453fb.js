// Original hack2hire:685df8f70807241a1a2453fb; inferred public-preview contract; qualification unknown.
"use strict";
class RateLimiter {
  constructor(rules) { this.rules = rules.map(([limit, window]) => ({limit, window, times:[], head:0})); }
  allow(timestamp) {
    let allowed = true;
    for (const rule of this.rules) {
      while (rule.head < rule.times.length && rule.times[rule.head] <= timestamp-rule.window) rule.head++;
      if (rule.times.length-rule.head >= rule.limit) allowed = false;
      if (rule.head > 1024 && rule.head*2 > rule.times.length) { rule.times = rule.times.slice(rule.head); rule.head = 0; }
    }
    if (allowed) for (const rule of this.rules) rule.times.push(timestamp);
    return allowed;
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "RateLimiter") throw new Error("exact constructor trace required");
  const instance = new RateLimiter(...argumentLists[0]), result = [null], allowed = new Set(["allow"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.RateLimiter = RateLimiter;
