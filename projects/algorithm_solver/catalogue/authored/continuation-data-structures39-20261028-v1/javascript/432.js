"use strict";

class Bucket {
  constructor(count) {
    this.count = count;
    this.keys = new Set();
    this.prev = null;
    this.next = null;
  }
}

function minKeyInSet(s) {
  let best = null;
  for (const k of s) {
    if (best === null || k < best) best = k;
  }
  return best === null ? "" : best;
}

class AllOne {
  constructor() {
    this.head = new Bucket(0);
    this.tail = new Bucket(0);
    this.head.next = this.tail;
    this.tail.prev = this.head;
    this.keyBucket = new Map();
  }
  _insertAfter(node, newNode) {
    const nxt = node.next;
    node.next = newNode;
    newNode.prev = node;
    newNode.next = nxt;
    nxt.prev = newNode;
    return newNode;
  }
  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
  inc(key) {
    if (!this.keyBucket.has(key)) {
      let first = this.head.next;
      if (first === this.tail || first.count !== 1) {
        first = this._insertAfter(this.head, new Bucket(1));
      }
      first.keys.add(key);
      this.keyBucket.set(key, first);
    } else {
      const cur = this.keyBucket.get(key);
      let nxt = cur.next;
      if (nxt === this.tail || nxt.count !== cur.count + 1) {
        nxt = this._insertAfter(cur, new Bucket(cur.count + 1));
      }
      nxt.keys.add(key);
      this.keyBucket.set(key, nxt);
      cur.keys.delete(key);
      if (cur.keys.size === 0) this._remove(cur);
    }
  }
  dec(key) {
    const cur = this.keyBucket.get(key);
    if (cur.count === 1) {
      this.keyBucket.delete(key);
    } else {
      let prv = cur.prev;
      if (prv === this.head || prv.count !== cur.count - 1) {
        prv = this._insertAfter(cur.prev, new Bucket(cur.count - 1));
      }
      prv.keys.add(key);
      this.keyBucket.set(key, prv);
    }
    cur.keys.delete(key);
    if (cur.keys.size === 0) this._remove(cur);
  }
  getMaxKey() {
    if (this.tail.prev === this.head) return "";
    return minKeyInSet(this.tail.prev.keys);
  }
  getMinKey() {
    if (this.head.next === this.tail) return "";
    return minKeyInSet(this.head.next.keys);
  }
}

function solve(operation_names, argument_lists) {
  const instance = new AllOne();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "inc") { instance.inc(args[0]); out.push(null); }
    else if (op === "dec") { instance.dec(args[0]); out.push(null); }
    else if (op === "getMaxKey") out.push(instance.getMaxKey());
    else if (op === "getMinKey") out.push(instance.getMinKey());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.AllOne = AllOne;
