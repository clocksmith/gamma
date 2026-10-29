"use strict";
// Hack2Hire 68ad7692cdaebe9459ce9a78 (Realtime Bot IP Detection) over an INFERRED spec; qualification unknown.

class DetectionSystem {
  constructor(maxRequests, windowSeconds) { this.limit = maxRequests; this.window = windowSeconds; this.recent = new Map(); }

  isBot(ip, timestamp) {
    let queue = this.recent.get(ip);
    if (queue === undefined) { queue = {times: [], head: 0}; this.recent.set(ip, queue); }
    queue.times.push(timestamp);
    const low = timestamp - this.window + 1;
    while (queue.times[queue.head] < low) queue.head++;
    if (queue.head > 1024 && queue.head * 2 > queue.times.length) { queue.times = queue.times.slice(queue.head); queue.head = 0; }
    return queue.times.length - queue.head > this.limit;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DetectionSystem" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new DetectionSystem(...argumentLists[0]);
  const allowed = new Set(["isBot"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.DetectionSystem = DetectionSystem;
