// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

class Solution {
  reverseKGroup(head, k) {
    const sentinel = new Link(head);
    let before = sentinel;
    while (true) {
      let end = before;
      for (let count = 0; count < k; count += 1) {
        end = end.next;
        if (end === null) {
          return sentinel.next;
        }
      }

      const after = end.next;
      const first = before.next;
      let previous = after;
      let current = first;
      while (current !== after) {
        const following = current.next;
        current.next = previous;
        previous = current;
        current = following;
      }
      before.next = end;
      before = first;
    }
  }
}
