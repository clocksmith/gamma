"use strict";
// Hack2Hire 699f70796e73e4abccc9b539 (Priority Expiry LRU Cache) over an INFERRED spec; qualification unknown.

// min-heap of [order value, access stamp, key]; stamps are unique, so keys never need comparing
const less = (a, b) => (a[0] !== b[0] ? a[0] < b[0] : a[1] < b[1]);

function heapPush(heap, entry) {
  heap.push(entry);
  for (let i = heap.length - 1; i > 0;) {
    const up = (i - 1) >> 1;
    if (!less(heap[i], heap[up])) break;
    [heap[up], heap[i]] = [heap[i], heap[up]]; i = up;
  }
}

function heapPop(heap) {
  const last = heap.pop();
  if (heap.length === 0) return;
  heap[0] = last;
  for (let i = 0; ;) {
    const l = 2 * i + 1, r = l + 1;
    let small = i;
    if (l < heap.length && less(heap[l], heap[small])) small = l;
    if (r < heap.length && less(heap[r], heap[small])) small = r;
    if (small === i) break;
    [heap[small], heap[i]] = [heap[i], heap[small]]; i = small;
  }
}

class PriorityExpiryLRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.items = new Map(); // key -> [value, priority, expiryTime, access stamp]
    this.byExpiry = []; this.byPriority = []; this.clock = 0;
  }

  touch(key, item) {
    this.clock += 1; item[3] = this.clock;
    heapPush(this.byExpiry, [item[2], this.clock, key]);
    heapPush(this.byPriority, [item[1], this.clock, key]);
  }

  top(heap) {
    while (heap.length) {
      const entry = heap[0], item = this.items.get(entry[2]);
      if (item !== undefined && item[3] === entry[1]) return entry;
      heapPop(heap);
    }
    return undefined;
  }

  get(key, currentTime) {
    const item = this.items.get(key);
    if (item === undefined) return -1;
    if (item[2] <= currentTime) { this.items.delete(key); return -1; }
    this.touch(key, item);
    return item[0];
  }

  set(key, value, priority, expiryTime, currentTime) {
    let item = this.items.get(key);
    if (item === undefined) {
      if (this.items.size === this.capacity) {
        const top = this.top(this.byExpiry);
        const victim = top[0] <= currentTime ? top[2] : this.top(this.byPriority)[2];
        this.items.delete(victim);
      }
      item = [value, priority, expiryTime, 0];
      this.items.set(key, item);
    } else {
      item[0] = value; item[1] = priority; item[2] = expiryTime;
    }
    this.touch(key, item);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PriorityExpiryLRUCache" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new PriorityExpiryLRUCache(...argumentLists[0]);
  const allowed = new Set(["get", "set"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PriorityExpiryLRUCache = PriorityExpiryLRUCache;
