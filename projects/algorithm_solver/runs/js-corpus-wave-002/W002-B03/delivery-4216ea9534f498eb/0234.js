function isPalindrome(head) {
  if (!head || !head.next) return true;
  let slow = head, fast = head;
  while (fast && fast.next) { slow = slow.next; fast = fast.next.next; }
  if (fast) slow = slow.next;
  let reverse = null;
  while (slow) { const next = slow.next; slow.next = reverse; reverse = slow; slow = next; }
  let first = head, second = reverse, equal = true;
  while (second) { if (first.val !== second.val) equal = false; first = first.next; second = second.next; }
  let restored = null;
  while (reverse) { const next = reverse.next; reverse.next = restored; restored = reverse; reverse = next; }
  return equal;
}
