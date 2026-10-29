"use strict";
function solve(root){let height=0,stack=[[root,1]];while(stack.length){const [n,d]=stack.pop();height=Math.max(height,d);if(n.left!=null)stack.push([n.left,d+1]);if(n.right!=null)stack.push([n.right,d+1]);}const width=2**height-1,out=Array.from({length:height},()=>new Array(width).fill(''));stack=[[root,0,0,width-1]];while(stack.length){const [n,d,l,r]=stack.pop(),m=Math.floor((l+r)/2);out[d][m]=String(n.val);if(n.left!=null)stack.push([n.left,d+1,l,m-1]);if(n.right!=null)stack.push([n.right,d+1,m+1,r]);}return out;}

function printTree(root){return solve(root);}
module.exports=solve;
module.exports.printTree=printTree;
