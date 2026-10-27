'use strict';
// 208. Implement Trie (Prefix Tree).
class Trie {
  constructor() { this.root = new Map(); }
  insert(word) {
    let node = this.root;
    for (const char of word) { if (!node.has(char)) node.set(char, new Map()); node = node.get(char); }
    node.set('', new Map());
  }
  search(word) {
    let node = this.root;
    for (const char of word) { if (!node.has(char)) return false; node = node.get(char); }
    return node.has('');
  }
  startsWith(prefix) {
    let node = this.root;
    for (const char of prefix) { if (!node.has(char)) return false; node = node.get(char); }
    return true;
  }
}
function solve(operations, args) {
  const trie = new Trie();
  return operations.map((operation, index) => operation === 'Trie' ? null : trie[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, Trie };
