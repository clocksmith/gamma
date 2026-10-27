'use strict';

// 382. Linked List Random Node.

class Solution {
  constructor(head) { this.head = head; }
  getRandom() {
    let selected = null, count = 0;
    for (let node = this.head; node !== null; node = node.next) {
      count += 1;
      if (Math.floor(Math.random() * count) === 0) selected = node.val;
    }
    return selected;
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Solution(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

if (typeof module !== 'undefined') module.exports = { solve, Solution };
