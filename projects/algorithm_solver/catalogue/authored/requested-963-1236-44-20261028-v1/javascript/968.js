"use strict";
function solve(root){const states=new Map(),stack=[[root,false]];let count=0;while(stack.length){const [n,seen]=stack.pop();if(n==null)continue;if(!seen){stack.push([n,true],[n.left,false],[n.right,false]);continue;}const l=states.get(n.left)??1,r=states.get(n.right)??1;if(l===0||r===0){states.set(n,2);count++;}else states.set(n,l===2||r===2?1:0);}return count+Number(states.get(root)===0);}

function minCameraCover(root){return solve(root);}
module.exports=solve;
module.exports.minCameraCover=minCameraCover;
