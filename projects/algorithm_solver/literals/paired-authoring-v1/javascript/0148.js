// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

function splitRun(head, size) {
  if (head === null) {
    return null;
  }
  for (let count = 1; count < size; count += 1) {
    if (head.next === null) {
      break;
    }
    head = head.next;
  }
  const remainder = head.next;
  head.next = null;
  return remainder;
}

function mergeAfter(tail, left, right) {
  while (left !== null && right !== null) {
    if (left.val <= right.val) {
      tail.next = left;
      left = left.next;
    } else {
      tail.next = right;
      right = right.next;
    }
    tail = tail.next;
  }
  tail.next = left !== null ? left : right;
  while (tail.next !== null) {
    tail = tail.next;
  }
  return tail;
}

class Solution {
  sortList(head) {
    let length = 0;
    let current = head;
    while (current !== null) {
      length += 1;
      current = current.next;
    }

    const sentinel = new Link(head);
    let run_size = 1;
    while (run_size < length) {
      let before = sentinel;
      current = sentinel.next;
      while (current !== null) {
        const left = current;
        const right = splitRun(left, run_size);
        current = splitRun(right, run_size);
        before = mergeAfter(before, left, right);
      }
      run_size *= 2;
    }
    return sentinel.next;
  }
}
