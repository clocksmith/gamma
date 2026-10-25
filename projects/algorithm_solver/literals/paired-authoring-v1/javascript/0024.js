// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

class Solution {
  swapPairs(head) {
    const sentinel = new Link(head);
    let before = sentinel;
    while (before.next !== null && before.next.next !== null) {
      const first = before.next;
      const second = first.next;
      first.next = second.next;
      second.next = first;
      before.next = second;
      before = first;
    }
    return sentinel.next;
  }
}
