function sortList(head) {
  if (head === null || head.next === null) {
    return head;
  }

  let length = 0;
  for (let node = head; node !== null; node = node.next) {
    length += 1;
  }

  function split(start, size) {
    if (start === null) {
      return null;
    }

    let tail = start;
    for (let index = 1; index < size && tail.next !== null; index += 1) {
      tail = tail.next;
    }

    const next = tail.next;
    tail.next = null;
    return next;
  }

  function merge(left, right) {
    const dummy = { next: null };
    let tail = dummy;

    while (left !== null && right !== null) {
      if (left.val <= right.val) {
        tail.next = left;
        left = left.next;
      } else {
        tail.next = right;
        right = right.next;
      }
      tail = tail.next;
    }

    tail.next = left === null ? right : left;
    while (tail.next !== null) {
      tail = tail.next;
    }

    return [dummy.next, tail];
  }

  const dummy = { next: head };

  for (let size = 1; size < length; size *= 2) {
    let previousTail = dummy;
    let current = dummy.next;

    while (current !== null) {
      const left = current;
      const right = split(left, size);
      current = split(right, size);

      const [mergedHead, mergedTail] = merge(left, right);
      previousTail.next = mergedHead;
      previousTail = mergedTail;
    }
  }

  return dummy.next;
}
