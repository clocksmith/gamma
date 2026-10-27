'use strict';

// 707. Design Linked List.

class _Node {
  constructor(value = 0) { this.value = value; this.previous = null; this.next = null; }
}
class MyLinkedList {
  constructor() {
    this.head = new _Node(); this.tail = new _Node(); this.head.next = this.tail; this.tail.previous = this.head; this.size = 0;
  }
  _at(index) {
    let node;
    if (index < Math.floor(this.size / 2)) {
      node = this.head.next; for (let i = 0; i < index; i += 1) node = node.next;
    } else {
      node = this.tail; for (let i = 0; i < this.size - index; i += 1) node = node.previous;
    }
    return node;
  }
  get(index) { return index < 0 || index >= this.size ? -1 : this._at(index).value; }
  addAtHead(val) { this.addAtIndex(0, val); }
  addAtTail(val) { this.addAtIndex(this.size, val); }
  addAtIndex(index, val) {
    if (index > this.size) return;
    index = Math.max(index, 0);
    const next = this._at(index), previous = next.previous, node = new _Node(val);
    node.previous = previous; node.next = next; previous.next = node; next.previous = node; this.size += 1;
  }
  deleteAtIndex(index) {
    if (index < 0 || index >= this.size) return;
    const node = this._at(index); node.previous.next = node.next; node.next.previous = node.previous; this.size -= 1;
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new MyLinkedList(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = MyLinkedList;

if (typeof module !== 'undefined') module.exports = { solve, MyLinkedList, Solution };
