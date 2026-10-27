'use strict';

// 642. Design Search Autocomplete System.

class _TrieNode {
  constructor() { this.children = new Map(); this.top = []; }
}
class AutocompleteSystem {
  constructor(sentences, times) {
    this.root = new _TrieNode(); this.frequency = new Map(); this.prefix = ''; this.cursor = this.root;
    sentences.forEach((sentence, i) => this._record(sentence, times[i]));
  }
  _record(sentence, count) {
    this.frequency.set(sentence, (this.frequency.get(sentence) || 0) + count);
    let node = this.root;
    for (const char of sentence) {
      if (!node.children.has(char)) node.children.set(char, new _TrieNode());
      node = node.children.get(char);
      if (!node.top.includes(sentence)) node.top.push(sentence);
      node.top.sort((a, b) => this.frequency.get(b) - this.frequency.get(a) || (a < b ? -1 : a > b ? 1 : 0));
      if (node.top.length > 3) node.top.length = 3;
    }
  }
  input(c) {
    if (c === '#') {
      if (this.prefix) this._record(this.prefix, 1);
      this.prefix = ''; this.cursor = this.root; return [];
    }
    this.prefix += c;
    if (this.cursor !== null) this.cursor = this.cursor.children.get(c) || null;
    return this.cursor === null ? [] : this.cursor.top.slice();
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new AutocompleteSystem(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = AutocompleteSystem;

if (typeof module !== 'undefined') module.exports = { solve, AutocompleteSystem, Solution };
