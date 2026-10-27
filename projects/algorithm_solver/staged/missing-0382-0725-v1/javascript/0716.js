'use strict';

// 716. Max Stack.

class _Node {
  constructor(value = 0, serial = 0) { this.value = value; this.serial = serial; this.index = -1; this.previous = null; this.next = null; }
}
class MaxStack {
  constructor() {
    this.head = new _Node(); this.tail = new _Node(); this.head.next = this.tail; this.tail.previous = this.head;
    this.heap = []; this.serial = 0;
  }
  _higher(a, b) { return a.value > b.value || (a.value === b.value && a.serial > b.serial); }
  _swap(i, j) {
    [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]]; this.heap[i].index = i; this.heap[j].index = j;
  }
  _up(index) {
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this._higher(this.heap[index], this.heap[parent])) break;
      this._swap(index, parent); index = parent;
    }
  }
  _down(index) {
    while (2 * index + 1 < this.heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < this.heap.length && this._higher(this.heap[child + 1], this.heap[child])) child += 1;
      if (!this._higher(this.heap[child], this.heap[index])) break;
      this._swap(index, child); index = child;
    }
  }
  _removeHeap(index) {
    const removed = this.heap[index], last = this.heap.pop();
    if (index < this.heap.length) {
      this.heap[index] = last; last.index = index;
      if (index > 0 && this._higher(last, this.heap[Math.floor((index - 1) / 2)])) this._up(index);
      else this._down(index);
    }
    removed.index = -1; return removed;
  }
  _unlink(node) { node.previous.next = node.next; node.next.previous = node.previous; }
  push(x) {
    const node = new _Node(x, this.serial++);
    node.previous = this.tail.previous; node.next = this.tail;
    this.tail.previous.next = node; this.tail.previous = node;
    node.index = this.heap.length; this.heap.push(node); this._up(node.index);
  }
  pop() { const node = this.tail.previous; this._unlink(node); this._removeHeap(node.index); return node.value; }
  top() { return this.tail.previous.value; }
  peekMax() { return this.heap[0].value; }
  popMax() { const node = this._removeHeap(0); this._unlink(node); return node.value; }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MaxStack(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MaxStack;

if (typeof module !== 'undefined') module.exports = { solve, MaxStack, Solution };
