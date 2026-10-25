// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

class Solution {
  partition(head, x) {
    const lower_sentinel = new Link();
    const upper_sentinel = new Link();
    let lower_tail = lower_sentinel;
    let upper_tail = upper_sentinel;
    let current = head;
    while (current !== null) {
      const next_node = current.next;
      current.next = null;
      if (current.val < x) {
        lower_tail.next = current;
        lower_tail = current;
      } else {
        upper_tail.next = current;
        upper_tail = current;
      }
      current = next_node;
    }

    lower_tail.next = upper_sentinel.next;
    return lower_sentinel.next;
  }
}
