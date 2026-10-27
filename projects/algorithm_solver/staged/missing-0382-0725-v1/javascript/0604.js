'use strict';

// 604. Design Compressed String Iterator.

class StringIterator {
  constructor(compressedString) { this.source = compressedString; this.index = 0; this.remaining = 0; this.char = ' '; }
  _load() {
    while (this.remaining === 0 && this.index < this.source.length) {
      this.char = this.source[this.index++];
      while (this.index < this.source.length && this.source[this.index] >= '0' && this.source[this.index] <= '9') {
        this.remaining = this.remaining * 10 + Number(this.source[this.index++]);
      }
    }
  }
  next() { this._load(); if (this.remaining === 0) return ' '; this.remaining -= 1; return this.char; }
  hasNext() { this._load(); return this.remaining > 0; }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new StringIterator(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = StringIterator;

if (typeof module !== 'undefined') module.exports = { solve, StringIterator, Solution };
