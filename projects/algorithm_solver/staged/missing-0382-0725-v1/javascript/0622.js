'use strict';

// 622. Design Circular Queue.

class MyCircularQueue {
  constructor(k) { this.data = Array(k).fill(0); this.capacity = k; this.head = 0; this.size = 0; }
  enQueue(value) {
    if (this.isFull()) return false;
    this.data[(this.head + this.size) % this.capacity] = value; this.size += 1; return true;
  }
  deQueue() { if (this.isEmpty()) return false; this.head = (this.head + 1) % this.capacity; this.size -= 1; return true; }
  Front() { return this.isEmpty() ? -1 : this.data[this.head]; }
  Rear() { return this.isEmpty() ? -1 : this.data[(this.head + this.size - 1) % this.capacity]; }
  isEmpty() { return this.size === 0; }
  isFull() { return this.size === this.capacity; }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MyCircularQueue(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MyCircularQueue;

if (typeof module !== 'undefined') module.exports = { solve, MyCircularQueue, Solution };
