"use strict";
function solve(root){const minimum=root.val,stack=[root];let second=Infinity;while(stack.length){const n=stack.pop();if(n.val>minimum)second=Math.min(second,n.val);if(n.left!=null)stack.push(n.left);if(n.right!=null)stack.push(n.right);}return second===Infinity?-1:second;}

function findSecondMinimumValue(root){return solve(root);}
module.exports=solve;
module.exports.findSecondMinimumValue=findSecondMinimumValue;
