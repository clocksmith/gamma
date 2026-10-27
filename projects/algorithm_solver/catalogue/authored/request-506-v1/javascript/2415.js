// Original candidate implementation. Contract: https://leetcode.com/problems/reverse-odd-levels-of-binary-tree/
"use strict";
function solve(root){let level=[root],depth=0;while(level.length){if(depth%2)for(let i=0;i<level.length/2;i++){const j=level.length-1-i;[level[i].val,level[j].val]=[level[j].val,level[i].val];}const next=[];for(const node of level){if(node.left)next.push(node.left);if(node.right)next.push(node.right);}level=next;depth++;}return root;}
module.exports = solve;
