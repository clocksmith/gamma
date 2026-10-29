"use strict";
function solve(root){let level=[root];const out=[];while(level.length){let sum=0;const next=[];for(const n of level){sum+=n.val;if(n.left!=null)next.push(n.left);if(n.right!=null)next.push(n.right);}out.push(sum/level.length);level=next;}return out;}

function averageOfLevels(root){return solve(root);}
module.exports=solve;
module.exports.averageOfLevels=averageOfLevels;
