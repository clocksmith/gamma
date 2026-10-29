"use strict";
// Hack2Hire 695d85f19c1c1f40daea73a0 (Design Token Limiter) over an INFERRED spec; qualification unknown.

class TokenLimiter {
  constructor() { this.users = new Map(); } // userId -> [maxTokens, refillAmount, refillInterval, tokens, lastRefill]

  setPolicy(userId, maxTokens, refillAmount, refillInterval, timestamp) {
    this.users.set(userId, [maxTokens, refillAmount, refillInterval, maxTokens, timestamp]);
  }

  refill(bucket, timestamp) {
    const due = Math.floor((timestamp - bucket[4]) / bucket[2]);
    if (due > 0) {
      bucket[3] = Math.min(bucket[0], bucket[3] + due * bucket[1]);
      bucket[4] += due * bucket[2];
    }
  }

  consume(userId, tokens, timestamp) {
    const bucket = this.users.get(userId);
    if (bucket === undefined) return false;
    this.refill(bucket, timestamp);
    if (bucket[3] >= tokens) { bucket[3] -= tokens; return true; }
    return false;
  }

  getTokens(userId, timestamp) {
    const bucket = this.users.get(userId);
    if (bucket === undefined) return -1;
    this.refill(bucket, timestamp);
    return bucket[3];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TokenLimiter" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TokenLimiter(...argumentLists[0]);
  const allowed = new Set(["setPolicy", "consume", "getTokens"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.TokenLimiter = TokenLimiter;
