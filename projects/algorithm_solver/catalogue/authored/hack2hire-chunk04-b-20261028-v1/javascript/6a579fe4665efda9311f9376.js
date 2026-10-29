"use strict";
// Hack2Hire 6a579fe4665efda9311f9376 (Chat Message Events Aggregation, level 2) over an INFERRED spec; qualification unknown.

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
  constructor(m) { this.m = m; this.users = new Map(); this.chats = new Map(); }

  trim(queue, timestamp) {
    const low = timestamp - this.m + 1;
    while (queue.size && queue.front() < low) queue.shift();
  }

  count(table, key, timestamp) {
    const queue = table.get(key);
    if (!queue) return 0;
    this.trim(queue, timestamp);
    if (!queue.size) { table.delete(key); return 0; }
    return queue.size;
  }

  recordEvent(timestamp, userId, chatId) {
    for (const [table, key] of [[this.users, userId], [this.chats, chatId]]) {
      let queue = table.get(key);
      if (!queue) { queue = new Queue(); table.set(key, queue); }
      queue.push(timestamp);
      this.trim(queue, timestamp);
    }
  }

  getUserCount(timestamp, userId) { return this.count(this.users, userId, timestamp); }

  getChatCount(timestamp, chatId) { return this.count(this.chats, chatId, timestamp); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ChatEventAggregator" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ChatEventAggregator(...argumentLists[0]);
  const allowed = new Set(["recordEvent", "getUserCount", "getChatCount"]);
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
