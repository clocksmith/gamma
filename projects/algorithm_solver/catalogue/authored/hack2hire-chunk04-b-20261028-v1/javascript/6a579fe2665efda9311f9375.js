"use strict";
// Hack2Hire 6a579fe2665efda9311f9375 (Chat Message Events Aggregation, level 1) over an INFERRED spec; qualification unknown.

// Array-backed FIFO with a moving head; compacted when the dead prefix dominates.
class Queue {
  constructor() { this.items = []; this.head = 0; }
  get size() { return this.items.length - this.head; }
  push(x) { this.items.push(x); }
  front() { return this.items[this.head]; }
  shift() {
    const x = this.items[this.head++];
    if (this.head > 1024 && this.head * 2 > this.items.length) { this.items = this.items.slice(this.head); this.head = 0; }
    return x;
  }
}

class ChatEventAggregator {
  constructor(m) { this.m = m; this.users = new Map(); }

  trim(queue, timestamp) {
    const low = timestamp - this.m + 1;
    while (queue.size && queue.front() < low) queue.shift();
  }

  recordEvent(timestamp, userId, chatId) {
    let queue = this.users.get(userId);
    if (!queue) { queue = new Queue(); this.users.set(userId, queue); }
    queue.push(timestamp);
    this.trim(queue, timestamp);
  }

  getUserCount(timestamp, userId) {
    const queue = this.users.get(userId);
    if (!queue) return 0;
    this.trim(queue, timestamp);
    if (!queue.size) { this.users.delete(userId); return 0; }
    return queue.size;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ChatEventAggregator" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ChatEventAggregator(...argumentLists[0]);
  const allowed = new Set(["recordEvent", "getUserCount"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ChatEventAggregator = ChatEventAggregator;
