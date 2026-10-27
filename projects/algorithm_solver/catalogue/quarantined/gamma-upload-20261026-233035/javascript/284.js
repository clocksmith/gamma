'use strict';
// 284. Peeking Iterator.
class PeekingIterator {
  constructor(iterator) {
    this.iterator = iterator;
    this.available = iterator.hasNext();
    this.cached = this.available ? iterator.next() : undefined;
  }
  peek() { return this.cached; }
  next() {
    const value = this.cached;
    this.available = this.iterator.hasNext();
    this.cached = this.available ? this.iterator.next() : undefined;
    return value;
  }
  hasNext() { return this.available; }
}
function solve(iterator, operations) {
  const peeking = new PeekingIterator(iterator);
  return operations.map(operation => peeking[operation]());
}
if (typeof module !== 'undefined') module.exports = { solve, PeekingIterator };
