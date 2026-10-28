"use strict";
class ListNode {constructor(val=0,next=null){this.val=val;this.next=next;}}
function solve(head) {
if(head===null||head.next===null)return;let slow=head,fast=head;while(fast.next!==null&&fast.next.next!==null){slow=slow.next;fast=fast.next.next;}let second=slow.next;slow.next=null;let previous=null;while(second!==null){const following=second.next;second.next=previous;previous=second;second=following;}let first=head;second=previous;while(second!==null){const firstNext=first.next,secondNext=second.next;first.next=second;second.next=firstNext;first=firstNext;second=secondNext;}return;
}
function reorderList(head) { return solve(head); }
class Solution {reorderList(head) { return solve(head); }}
module.exports=solve;
module.exports.reorderList=reorderList;
module.exports.Solution=Solution;
module.exports.ListNode=ListNode;
