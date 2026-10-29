"use strict";
function solve(root){const records=[],stack=[[root,0,0]];while(stack.length){const [n,r,c]=stack.pop();records.push([c,r,n.val]);if(n.left!=null)stack.push([n.left,r+1,c-1]);if(n.right!=null)stack.push([n.right,r+1,c+1]);}records.sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);const out=[];let prev=null;for(const [c,,v]of records){if(c!==prev){out.push([]);prev=c;}out[out.length-1].push(v);}return out;}

function verticalTraversal(root){return solve(root);}
module.exports=solve;
module.exports.verticalTraversal=verticalTraversal;
