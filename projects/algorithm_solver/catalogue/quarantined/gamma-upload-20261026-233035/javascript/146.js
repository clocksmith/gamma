'use strict';
// 146. LRU Cache.
class Node {
  constructor(key = 0, value = 0) { this.key = key; this.value = value; this.previous = null; this.next = null; }
}
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity; this.nodes = new Map();
    this.head = new Node(); this.tail = new Node();
    this.head.next = this.tail; this.tail.previous = this.head;
  }
  remove(node) { node.previous.next = node.next; node.next.previous = node.previous; }
  append(node) {
    node.previous = this.tail.previous; node.next = this.tail;
    this.tail.previous.next = node; this.tail.previous = node;
  }
  get(key) {
    if (!this.nodes.has(key)) return -1;
    const node = this.nodes.get(key); this.remove(node); this.append(node); return node.value;
  }
  put(key, value) {
    if (this.nodes.has(key)) {
      const node = this.nodes.get(key); node.value = value; this.remove(node); this.append(node); return;
    }
    const node = new Node(key, value); this.nodes.set(key, node); this.append(node);
    if (this.nodes.size > this.capacity) {
      const oldest = this.head.next; this.remove(oldest); this.nodes.delete(oldest.key);
    }
  }
}
function solve(operations, args) {
  const result = []; let cache = null;
  for (let index = 0; index < operations.length; index += 1) {
    if (operations[index] === 'LRUCache') { cache = new LRUCache(...args[index]); result.push(null); }
    else result.push(cache[operations[index]](...args[index]));
  }
  return result;
}
if (typeof module !== 'undefined') module.exports = { solve, LRUCache };
