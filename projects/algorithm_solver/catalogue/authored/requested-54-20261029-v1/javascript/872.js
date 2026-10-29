"use strict";
function solve(root1,root2){function leaves(root){const q=[root],out=[];while(q.length){const node=q.pop();if(!node.left&&!node.right)out.push(node.val);else{if(node.right)q.push(node.right);if(node.left)q.push(node.left);}}return out;}
 const a=leaves(root1),b=leaves(root2);return a.length===b.length&&a.every((v,i)=>v===b[i]);
}

function leafSimilar(root1, root2) { return solve(root1, root2); }
module.exports=solve;
module.exports.leafSimilar=leafSimilar;
