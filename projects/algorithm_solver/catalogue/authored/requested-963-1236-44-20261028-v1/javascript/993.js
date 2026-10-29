"use strict";
function solve(root,x,y){let level=[[root,null]];while(level.length){const found=new Map(),next=[];for(const [n,p]of level){if(n.val===x||n.val===y)found.set(n.val,p);if(n.left!=null)next.push([n.left,n]);if(n.right!=null)next.push([n.right,n]);}if(found.size)return found.size===2&&found.get(x)!==found.get(y);level=next;}return false;}

function isCousins(root, x, y){return solve(root, x, y);}
module.exports=solve;
module.exports.isCousins=isCousins;
