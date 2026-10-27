'use strict';

// 432. All O`one Data Structure.

class Bucket {
  constructor(count) { this.count = count; this.keys = new Set(); this.previous = null; this.next = null; }
}

class AllOne {
  constructor() {
    this.head = new Bucket(0); this.tail = new Bucket(0);
    this.head.next = this.tail; this.tail.previous = this.head;
    this.owner = new Map();
  }
  _after(previous, count) {
    const node = new Bucket(count);
    node.previous = previous; node.next = previous.next;
    previous.next.previous = node; previous.next = node;
    return node;
  }
  _discardEmpty(node) {
    if (node !== this.head && node !== this.tail && node.keys.size === 0) {
      node.previous.next = node.next; node.next.previous = node.previous;
    }
  }
  inc(key) {
    const source = this.owner.get(key) || this.head;
    let target = source.next;
    if (target === this.tail || target.count !== source.count + 1) target = this._after(source, source.count + 1);
    target.keys.add(key); this.owner.set(key, target);
    if (source !== this.head) { source.keys.delete(key); this._discardEmpty(source); }
  }
  dec(key) {
    const source = this.owner.get(key);
    if (source.count === 1) this.owner.delete(key);
    else {
      let target = source.previous;
      if (target === this.head || target.count !== source.count - 1) target = this._after(source.previous, source.count - 1);
      target.keys.add(key); this.owner.set(key, target);
    }
    source.keys.delete(key); this._discardEmpty(source);
  }
  getMaxKey() { return this.tail.previous.keys.values().next().value || ''; }
  getMinKey() { return this.head.next.keys.values().next().value || ''; }
}


function solve(operations, args) {
  // Replay the native LeetCode interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new AllOne(...args[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...args[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = AllOne;
if (typeof module !== 'undefined') module.exports = { solve, Solution, AllOne };
