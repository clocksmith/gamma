function oddEvenList(head) {
  if (head === null || head.next === null) return head;

  let oddTail = head;
  let evenTail = head.next;
  const evenHead = evenTail;

  while (evenTail !== null && evenTail.next !== null) {
    oddTail.next = evenTail.next;
    oddTail = oddTail.next;
    evenTail.next = oddTail.next;
    evenTail = evenTail.next;
  }
  oddTail.next = evenHead;
  return head;
}
