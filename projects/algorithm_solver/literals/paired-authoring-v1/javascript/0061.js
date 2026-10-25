// External ListNode shape: {val: number, next: ListNode | null}.
class Solution {
  rotateRight(head, k) {
    if (head === null || head.next === null) {
      return head;
    }

    let length = 1;
    let tail = head;
    while (tail.next !== null) {
      tail = tail.next;
      length += 1;
    }
    const rotation = k % length;
    if (rotation === 0) {
      return head;
    }

    let new_tail = head;
    for (let count = 0; count < length - rotation - 1; count += 1) {
      new_tail = new_tail.next;
    }
    const new_head = new_tail.next;
    tail.next = head;
    new_tail.next = null;
    return new_head;
  }
}
