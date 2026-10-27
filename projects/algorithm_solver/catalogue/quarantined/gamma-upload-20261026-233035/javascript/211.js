'use strict';
// 211. Design Add and Search Words Data Structure.
class WordDictionary {
  constructor() { this.root = new Map(); }
  addWord(word) {
    let node = this.root;
    for (const char of word) { if (!node.has(char)) node.set(char, new Map()); node = node.get(char); }
    node.set('', new Map());
  }
  search(word) {
    function visit(index, node) {
      if (index === word.length) return node.has('');
      const char = word[index];
      if (char === '.') {
        for (const [key, child] of node) if (key !== '' && visit(index + 1, child)) return true;
        return false;
      }
      return node.has(char) && visit(index + 1, node.get(char));
    }
    return visit(0, this.root);
  }
}
function solve(operations, args) {
  const dictionary = new WordDictionary();
  return operations.map((operation, index) => operation === 'WordDictionary' ? null : dictionary[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, WordDictionary };
