// External nodes have val and next; absent next is null.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}


class Solution {
  removeZeroSumSublists(head) {
    const sentinel = new Link(head);
    const last = new Map([[0, sentinel]]);
    let total = 0;
    let current = head;
    while (current !== null) {
      total += current.val;
      last.set(total, current);
      current = current.next;
    }
    current = sentinel;
    total = 0;
    while (current !== null) {
      current.next = last.get(total).next;
      current = current.next;
      if (current !== null) {
        total += current.val;
      }
    }
    return sentinel.next;
  }
}
