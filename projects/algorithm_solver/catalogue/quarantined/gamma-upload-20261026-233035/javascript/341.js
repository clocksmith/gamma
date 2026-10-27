'use strict';
// 341. Flatten Nested List Iterator.
class NestedIterator {
  constructor(nestedList) { this.stack = nestedList.slice().reverse(); }
  advance() {
    while (this.stack.length && !this.stack[this.stack.length - 1].isInteger()) {
      this.stack.push(...this.stack.pop().getList().slice().reverse());
    }
  }
  next() { this.advance(); return this.stack.pop().getInteger(); }
  hasNext() { this.advance(); return this.stack.length > 0; }
}
function solve(nestedList) {
  const iterator = new NestedIterator(nestedList); const result = [];
  while (iterator.hasNext()) result.push(iterator.next());
  return result;
}
if (typeof module !== 'undefined') module.exports = { solve, NestedIterator };
