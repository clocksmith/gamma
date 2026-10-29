"use strict";
function solve(root){const identities=new Map(),counts=new Map(),memo=new Map(),out=[],stack=[[root,false]];while(stack.length){const [n,visited]=stack.pop();if(n==null)continue;if(!visited){stack.push([n,true],[n.right,false],[n.left,false]);continue;}const key=JSON.stringify([n.val,memo.get(n.left)||0,memo.get(n.right)||0]);if(!identities.has(key))identities.set(key,identities.size+1);const id=identities.get(key);memo.set(n,id);const count=(counts.get(id)||0)+1;counts.set(id,count);if(count===2)out.push(n);}return out;}

function findDuplicateSubtrees(root){return solve(root);}
module.exports=solve;
module.exports.findDuplicateSubtrees=findDuplicateSubtrees;
