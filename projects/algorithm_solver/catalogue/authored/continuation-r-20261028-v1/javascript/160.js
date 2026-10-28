class ListNode {
  constructor(val) {
    this.val = val;
    this.next = null;
  }
}
function getIntersectionNode(headA, headB) {
  let first = headA, second = headB;
  while (first !== second) {
    first = first === null ? headB : first.next;
    second = second === null ? headA : second.next;
  }
  return first;
}
module.exports = {getIntersectionNode, ListNode};
