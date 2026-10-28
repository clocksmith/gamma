"use strict";
class ListNode {constructor(val){this.val=val;this.next=null;}}
function solve(head) {
let slow=head,fast=head;while(fast!==null&&fast.next!==null){slow=slow.next;fast=fast.next.next;if(slow===fast)return true;}return false;
}
function hasCycle(head) { return solve(head); }
class Solution {hasCycle(head) { return solve(head); }}
module.exports=solve;
module.exports.hasCycle=hasCycle;
module.exports.Solution=Solution;
module.exports.ListNode=ListNode;
