"use strict";
function ListNode(val=0,next=null){this.val=val;this.next=next;}function solve(list1,a,b,list2){const dummy=new ListNode();let tail=dummy,node=list1,index=0;while(node!=null){if(index===a){let other=list2;while(other!=null){tail.next=new ListNode(other.val);tail=tail.next;other=other.next;}}if(index<a||index>b){tail.next=new ListNode(node.val);tail=tail.next;}node=node.next;index++;}return dummy.next;}

function mergeInBetween(list1, a, b, list2){return solve(list1, a, b, list2);}
module.exports=solve;
module.exports.mergeInBetween=mergeInBetween;
module.exports.ListNode=ListNode;
