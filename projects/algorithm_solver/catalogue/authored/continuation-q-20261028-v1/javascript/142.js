"use strict";
class ListNode {constructor(val){this.val=val;this.next=null;}}
function solve(head) {
let slow=head,fast=head;while(fast!==null&&fast.next!==null){slow=slow.next;fast=fast.next.next;if(slow===fast){let entry=head;while(entry!==slow){entry=entry.next;slow=slow.next;}return entry;}}return null;
}
function detectCycle(head) { return solve(head); }
class Solution {detectCycle(head) { return solve(head); }}
module.exports=solve;
module.exports.detectCycle=detectCycle;
module.exports.Solution=Solution;
module.exports.ListNode=ListNode;
