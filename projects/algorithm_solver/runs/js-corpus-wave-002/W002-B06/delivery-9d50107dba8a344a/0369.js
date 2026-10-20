function plusOne(head) {
  const dummy = { val: 0, next: head };
  let lastNotNine = dummy;
  let current = head;

  while (current !== null) {
    if (current.val !== 9) lastNotNine = current;
    current = current.next;
  }
  lastNotNine.val++;
  current = lastNotNine.next;
  while (current !== null) {
    current.val = 0;
    current = current.next;
  }
  return dummy.val === 1 ? dummy : dummy.next;
}
