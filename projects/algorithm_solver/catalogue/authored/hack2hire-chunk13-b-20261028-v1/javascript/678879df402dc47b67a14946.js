"use strict";
// Hack2Hire 678879df402dc47b67a14946 (Search History System) over an INFERRED spec; qualification unknown.

class SearchHistory {
  constructor(capacity) {
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = {term: null, prev: null, next: null}; // most recent side
    this.tail = {term: null, prev: null, next: null}; // least recent side
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  unlink(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }

  pushFront(node) {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next.prev = node;
    this.head.next = node;
  }

  add(term) {
    let node = this.nodes.get(term);
    if (node !== undefined) this.unlink(node);
    else { node = {term, prev: null, next: null}; this.nodes.set(term, node); }
    this.pushFront(node);
    if (this.nodes.size > this.capacity) {
      const oldest = this.tail.prev;
      this.unlink(oldest);
      this.nodes.delete(oldest.term);
    }
  }

  getTopK(k) {
    const out = [];
    for (let node = this.head.next; node !== this.tail && out.length < k; node = node.next) out.push(node.term);
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SearchHistory" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new SearchHistory(...argumentLists[0]);
  const allowed = new Set(["add", "getTopK"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SearchHistory = SearchHistory;
