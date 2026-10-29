"use strict";
function ListNode(val,next){this.val=val===undefined?0:val;this.next=next===undefined?null:next;}
function solve(head, nums) {
const members=new Set(nums);let count=0;for(let node=head;node!==null&&node!==undefined;node=node.next){if(members.has(node.val)&&(node.next===null||node.next===undefined||!members.has(node.next.val)))count++;}return count;
}
function numComponents(head, nums) { return solve(head, nums); }
class Solution {numComponents(head, nums) { return solve(head, nums); }}
module.exports=solve;
module.exports.numComponents=numComponents;
module.exports.Solution=Solution;
module.exports.ListNode=ListNode;
