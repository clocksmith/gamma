"use strict";
// Hack2Hire 68d89bb279db2fbcd7d7db16 (Palindrome Stream Tracker) over an INFERRED spec; qualification unknown.

class PalindromeStream {
  constructor() {
    // palindromic tree: node 0 has length -1, node 1 is the empty palindrome
    this.length = [-1, 0];
    this.link = [0, 0];
    this.edges = [new Map(), new Map()];
    this.chars = [];
    this.last = 1;
  }

  extendFrom(node, i, c) {
    for (;;) {
      const j = i - 1 - this.length[node];
      if (j >= 0 && this.chars[j] === c) return node;
      node = this.link[node];
    }
  }

  track(c) {
    this.chars.push(c);
    const i = this.chars.length - 1;
    const node = this.extendFrom(this.last, i, c);
    const existing = this.edges[node].get(c);
    if (existing !== undefined) { this.last = existing; return; }
    const size = this.length[node] + 2;
    const suffix = size === 1 ? 1 : this.edges[this.extendFrom(this.link[node], i, c)].get(c);
    this.length.push(size);
    this.link.push(suffix);
    this.edges.push(new Map());
    const created = this.length.length - 1;
    this.edges[node].set(c, created);
    this.last = created;
  }

  isPalindrome() {
    return this.length[this.last] === this.chars.length;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PalindromeStream" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new PalindromeStream(...argumentLists[0]);
  const allowed = new Set(["track", "isPalindrome"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PalindromeStream = PalindromeStream;
