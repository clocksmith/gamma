"use strict";
function solve(head){const out=[],stack=[];let node=head;while(node!=null){const i=out.length;out.push(0);while(stack.length&&stack[stack.length-1][1]<node.val)out[stack.pop()[0]]=node.val;stack.push([i,node.val]);node=node.next;}return out;}

function nextLargerNodes(head){return solve(head);}
module.exports=solve;
module.exports.nextLargerNodes=nextLargerNodes;
