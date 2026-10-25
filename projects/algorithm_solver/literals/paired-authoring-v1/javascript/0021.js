// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

class Solution {
  mergeTwoLists(list1, list2) {
    const sentinel = new Link();
    let tail = sentinel;
    while (list1 !== null && list2 !== null) {
      if (list1.val <= list2.val) {
        tail.next = list1;
        list1 = list1.next;
      } else {
        tail.next = list2;
        list2 = list2.next;
      }
      tail = tail.next;
    }

    if (list1 !== null) {
      tail.next = list1;
    } else {
      tail.next = list2;
    }
    return sentinel.next;
  }
}
