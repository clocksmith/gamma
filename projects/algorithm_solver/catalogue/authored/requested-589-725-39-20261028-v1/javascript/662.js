"use strict";
function solve(root){let level=[[root,0]],answer=0;while(level.length){const base=level[0][1];answer=Math.max(answer,level[level.length-1][1]-base+1);const next=[];for(const [n,pos]of level){const p=pos-base;if(n.left!=null)next.push([n.left,2*p]);if(n.right!=null)next.push([n.right,2*p+1]);}level=next;}return answer;}

function widthOfBinaryTree(root){return solve(root);}
module.exports=solve;
module.exports.widthOfBinaryTree=widthOfBinaryTree;
