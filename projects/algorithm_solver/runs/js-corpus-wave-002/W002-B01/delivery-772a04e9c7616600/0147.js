function insertionSortList(head) {
  const dummy = { next: null };
  let current = head;

  while (current !== null) {
    const next = current.next;
    let previous = dummy;

    while (
      previous.next !== null &&
      previous.next.val <= current.val
    ) {
      previous = previous.next;
    }

    current.next = previous.next;
    previous.next = current;
    current = next;
  }

  return dummy.next;
}
