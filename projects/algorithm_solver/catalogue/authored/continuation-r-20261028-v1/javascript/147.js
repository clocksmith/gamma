class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}
function insertionSortList(head) {
  if (head === null) return null;
  const dummy = new ListNode(0, head);
  let lastSorted = head, current = head.next;
  while (current !== null) {
    if (lastSorted.val <= current.val) {
      lastSorted = current;
    } else {
      let previous = dummy;
      while (previous.next.val <= current.val) previous = previous.next;
      lastSorted.next = current.next;
      current.next = previous.next;
      previous.next = current;
    }
    current = lastSorted.next;
  }
  return dummy.next;
}
module.exports = {insertionSortList, ListNode};
