"use strict";
function solve(root){if(root==null)return 0;const down=new Map(),stack=[[root,false]];let answer=0;while(stack.length){const [n,visited]=stack.pop();if(n==null)continue;if(!visited){stack.push([n,true],[n.right,false],[n.left,false]);continue;}const l=n.left!=null&&n.left.val===n.val?down.get(n.left)+1:0,r=n.right!=null&&n.right.val===n.val?down.get(n.right)+1:0;answer=Math.max(answer,l+r);down.set(n,Math.max(l,r));}return answer;}

function longestUnivaluePath(root){return solve(root);}
module.exports=solve;
module.exports.longestUnivaluePath=longestUnivaluePath;
