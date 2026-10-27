// Original candidate implementation. Contract: https://leetcode.com/problems/count-nodes-equal-to-average-of-subtree/
"use strict";
function solve(root){const stack=[[root,false]],data=new Map();let answer=0;while(stack.length){const [node,done]=stack.pop();if(!node)continue;if(!done){stack.push([node,true],[node.right,false],[node.left,false]);}else{const [ls,lc]=data.get(node.left)||[0,0],[rs,rc]=data.get(node.right)||[0,0],total=ls+rs+node.val,count=lc+rc+1;data.set(node,[total,count]);if(Math.floor(total/count)===node.val)answer++;}}return answer;}
module.exports = solve;
