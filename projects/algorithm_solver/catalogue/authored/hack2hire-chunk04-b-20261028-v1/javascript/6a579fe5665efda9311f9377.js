"use strict";
// Hack2Hire 6a579fe5665efda9311f9377 (Chat Message Events Aggregation, level 3) over an INFERRED spec; qualification unknown.

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
  constructor(m) { this.m = m; this.users = new Map(); this.chats = new Map(); } // chatId -> {queue of [t, user], multiplicity}

  trimUser(userId, timestamp) {
    const queue = this.users.get(userId);
    if (!queue) return 0;
    const low = timestamp - this.m + 1;
    while (queue.size && queue.front() < low) queue.shift();
    if (!queue.size) { this.users.delete(userId); return 0; }
    return queue.size;
  }

  trimChat(chatId, timestamp) {
    const entry = this.chats.get(chatId);
    if (!entry) return null;
    const low = timestamp - this.m + 1;
    while (entry.queue.size && entry.queue.front()[0] < low) {
      const user = entry.queue.shift()[1];
      const left = entry.multiplicity.get(user) - 1;
      if (left) entry.multiplicity.set(user, left); else entry.multiplicity.delete(user);
    }
    if (!entry.queue.size) { this.chats.delete(chatId); return null; }
    return entry;
  }

  recordEvent(timestamp, userId, chatId) {
    let queue = this.users.get(userId);
    if (!queue) { queue = new Queue(); this.users.set(userId, queue); }
    queue.push(timestamp);
    this.trimUser(userId, timestamp);
    let entry = this.chats.get(chatId);
    if (!entry) { entry = {queue: new Queue(), multiplicity: new Map()}; this.chats.set(chatId, entry); }
    entry.queue.push([timestamp, userId]);
    entry.multiplicity.set(userId, (entry.multiplicity.get(userId) || 0) + 1);
    this.trimChat(chatId, timestamp);
  }

  getUserCount(timestamp, userId) { return this.trimUser(userId, timestamp); }

  getChatCount(timestamp, chatId) {
    const entry = this.trimChat(chatId, timestamp);
    return entry ? entry.queue.size : 0;
  }

  getChatUserCount(timestamp, chatId) {
    const entry = this.trimChat(chatId, timestamp);
    return entry ? entry.multiplicity.size : 0;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ChatEventAggregator" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ChatEventAggregator(...argumentLists[0]);
  const allowed = new Set(["recordEvent", "getUserCount", "getChatCount", "getChatUserCount"]);
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
