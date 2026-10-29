"use strict";
// Hack2Hire 694609632c048134ada83559 (Design Dual Circuit Breakers) over an INFERRED spec; qualification unknown.

class Breaker {
  constructor(threshold, cooldown) {
    this.threshold = threshold;
    this.cooldown = cooldown;
    this.isOpen = false;
    this.opened = 0;
    this.failures = 0;
  }

  allows(t) {
    return !this.isOpen || t - this.opened >= this.cooldown;
  }

  report(t, ok) {
    if (ok) {
      this.isOpen = false;
      this.failures = 0;
    } else if (this.isOpen) {
      this.opened = t;
    } else {
      this.failures += 1;
      if (this.failures >= this.threshold) {
        this.isOpen = true;
        this.opened = t;
        this.failures = 0;
      }
    }
  }
}

class DualCircuitBreaker {
  constructor(failureThreshold, cooldown) {
    this.primary = new Breaker(failureThreshold, cooldown);
    this.secondary = new Breaker(failureThreshold, cooldown);
  }

  request(timestamp, primaryOk, secondaryOk) {
    let attempted = false;
    if (this.primary.allows(timestamp)) {
      attempted = true;
      this.primary.report(timestamp, primaryOk);
      if (primaryOk) return "PRIMARY";
    }
    if (this.secondary.allows(timestamp)) {
      this.secondary.report(timestamp, secondaryOk);
      return secondaryOk ? "SECONDARY" : "FAILED";
    }
    return attempted ? "FAILED" : "BLOCKED";
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DualCircuitBreaker" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new DualCircuitBreaker(...argumentLists[0]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "request") throw new Error("unknown method");
    result.push(instance.request(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.DualCircuitBreaker = DualCircuitBreaker;
