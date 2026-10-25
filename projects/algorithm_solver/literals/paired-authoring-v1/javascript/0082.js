// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

class Solution {
  deleteDuplicates(head) {
    const sentinel = new Link(head);
    let before = sentinel;
    let current = head;
    while (current !== null) {
      let after = current.next;
      while (after !== null && after.val === current.val) {
        after = after.next;
      }
      if (current.next === after) {
        before = current;
      } else {
        before.next = after;
      }
      current = after;
    }
    return sentinel.next;
  }
}
