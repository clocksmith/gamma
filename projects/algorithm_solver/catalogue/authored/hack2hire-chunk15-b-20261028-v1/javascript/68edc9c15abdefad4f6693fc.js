"use strict";
// Hack2Hire 68edc9c15abdefad4f6693fc (Event Logger with Rate Limiting) over an INFERRED spec; qualification unknown.

class EventLogger {
  constructor(window) {
    this.window = window;
    this.last = new Map();
  }

  logEvent(name, timestamp) {
    const previous = this.last.get(name);
    if (previous !== undefined && timestamp - previous < this.window) return false;
    this.last.set(name, timestamp);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "EventLogger" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new EventLogger(...argumentLists[0]);
  const allowed = new Set(["logEvent"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.EventLogger = EventLogger;
