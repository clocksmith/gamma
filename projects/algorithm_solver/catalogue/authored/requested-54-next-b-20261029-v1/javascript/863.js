"use strict";
function solve(root,target,k){const graph=new Map(),stack=[root];
 while(stack.length){const node=stack.pop();if(!graph.has(node.val))graph.set(node.val,[]);for(const child of [node.left,node.right])if(child!==null&&child!==undefined){if(!graph.has(child.val))graph.set(child.val,[]);graph.get(child.val).push(node.val);graph.get(node.val).push(child.val);stack.push(child);}}
 const queue=[[target,0]],seen=new Set([target]),out=[];
 for(let head=0;head<queue.length;head++){const [value,distance]=queue[head];if(distance===k){out.push(value);continue;}for(const neighbor of graph.get(value))if(!seen.has(neighbor)){seen.add(neighbor);queue.push([neighbor,distance+1]);}}
 return out;
}
function distanceK(root,target,k){return solve(root,target,k);}
module.exports=solve;module.exports.distanceK=distanceK;
