'use strict';
// 237. Delete Node in a Linked List.
class ListNode { constructor(val = 0, next = null) { this.val = val; this.next = next; } }
function solve(node) { node.val = node.next.val; node.next = node.next.next; }
const deleteNode = solve;
class Solution { deleteNode(node) { solve(node); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteNode, ListNode };
