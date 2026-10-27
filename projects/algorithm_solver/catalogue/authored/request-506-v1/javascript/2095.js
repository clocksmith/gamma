// Original candidate implementation. Contract: https://leetcode.com/problems/delete-the-middle-node-of-a-linked-list/
"use strict";
function solve(head){if(head.next==null)return null;let slow=head,fast=head,previous=null;while(fast&&fast.next){previous=slow;slow=slow.next;fast=fast.next.next;}previous.next=slow.next;return head;}
module.exports = solve;
