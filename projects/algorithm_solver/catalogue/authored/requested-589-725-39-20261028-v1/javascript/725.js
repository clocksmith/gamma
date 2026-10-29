"use strict";
function ListNode(val=0,next=null){this.val=val;this.next=next;}function solve(head,k){let length=0,node=head;while(node!=null){length++;node=node.next;}const base=Math.floor(length/k),extra=length%k,result=[];node=head;for(let part=0;part<k;part++){const dummy=new ListNode();let tail=dummy;for(let i=0;i<base+Number(part<extra);i++){tail.next=new ListNode(node.val);tail=tail.next;node=node.next;}result.push(dummy.next);}return result;}

function splitListToParts(head, k){return solve(head, k);}
module.exports=solve;
module.exports.splitListToParts=splitListToParts;
module.exports.ListNode=ListNode;
