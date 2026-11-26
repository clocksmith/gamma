'use strict';

class Node {
  constructor(key) {
    this.key = key;
    this.next = null;
    this.prev = null;
  }
}

class List {
  constructor() {
    this.nil = new Node();
    this.nil.next = this.nil;
    this.nil.prev = this.nil;
  }

  deleteFirst() {
    this.deleteNode(this.nil.next);
  }

  deleteKey(key) {
    this.deleteNode(this.listSearch(key));
  }

  deleteLast() {
    this.deleteNode(this.nil.prev);
  }

  deleteNode(node) {
    if (node === this.nil) {
      return;
    }
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }

  insert(key) {
    const node = new Node(key);
    node.next = this.nil.next;
    this.nil.next.prev = node;
    this.nil.next = node;
    node.prev = this.nil;
  }

  listSearch(key) {
    // let node = this.nil;
    // while (node.next !== this.nil && node.key !== key) {
    let curr = this.nil.next;
    while (curr !== this.nil && curr.key !== key) {
      curr = curr.next;
    }
    return curr;
  }

  toArray() {
    let curr = this.nil.next;
    const arr = [];
    while (curr !== this.nil) {
      arr.push(curr.key);
      curr = curr.next;
    }
    return arr;
  }
}

const main = input => {
  input = input.split('\n');
  input.shift();
  const list = new List();
  input.forEach(v => {
    const tmp = v.split(' ');
    const command = tmp[0];
    const key = tmp[1];
    switch (command) {
      case 'insert':
        list.insert(key);
        break;
      case 'delete':
        list.deleteKey(key);
        break;
      case 'deleteFirst':
        list.deleteFirst();
        break;
      case 'deleteLast':
        list.deleteLast();
        break;
    }
  });

  console.log(list.toArray().join(' '));
};

main(require('fs').readFileSync('/dev/stdin', 'utf8'));

// function myInsert(x, arr) {
//   arr.unshift(x);
//   return arr;
// }
// function myDelete(x, arr) {
//   const i = arr.findIndex(v => v === x);
//   if (i > -1) {
//     arr.splice(i, 1);
//   }
//   return arr;
// }
// function myDeleteFirst(arr) {
//   arr.shift();
//   return arr;
// }
// function myDeleteLast(arr) {
//   arr.pop();
//   return arr;
// }

