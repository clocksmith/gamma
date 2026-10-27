'use strict';

// 677. Map Sum Pairs.

class _TrieNode {
  constructor() { this.children = new Map(); this.total = 0; }
}
class MapSum {
  constructor() { this.values = new Map(); this.root = new _TrieNode(); }
  insert(key, val) {
    const delta = val - (this.values.get(key) || 0);
    this.values.set(key, val);
    let node = this.root;
    node.total += delta;
    for (const char of key) {
      if (!node.children.has(char)) node.children.set(char, new _TrieNode());
      node = node.children.get(char); node.total += delta;
    }
  }
  sum(prefix) {
    let node = this.root;
    for (const char of prefix) { node = node.children.get(char); if (!node) return 0; }
    return node.total;
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MapSum(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MapSum;

if (typeof module !== 'undefined') module.exports = { solve, MapSum, Solution };
