'use strict';

// 641. Design Circular Deque.

class MyCircularDeque {
  constructor(k) { this.data = Array(k).fill(0); this.capacity = k; this.head = 0; this.size = 0; }
  insertFront(value) {
    if (this.isFull()) return false;
    this.head = (this.head - 1 + this.capacity) % this.capacity;
    this.data[this.head] = value; this.size += 1; return true;
  }
  insertLast(value) {
    if (this.isFull()) return false;
    this.data[(this.head + this.size) % this.capacity] = value; this.size += 1; return true;
  }
  deleteFront() { if (this.isEmpty()) return false; this.head = (this.head + 1) % this.capacity; this.size -= 1; return true; }
  deleteLast() { if (this.isEmpty()) return false; this.size -= 1; return true; }
  getFront() { return this.isEmpty() ? -1 : this.data[this.head]; }
  getRear() { return this.isEmpty() ? -1 : this.data[(this.head + this.size - 1) % this.capacity]; }
  isEmpty() { return this.size === 0; }
  isFull() { return this.size === this.capacity; }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MyCircularDeque(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MyCircularDeque;

if (typeof module !== 'undefined') module.exports = { solve, MyCircularDeque, Solution };
