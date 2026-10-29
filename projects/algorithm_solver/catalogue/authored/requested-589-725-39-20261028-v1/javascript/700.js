"use strict";
function solve(root,val){let node=root;while(node!=null&&node.val!==val)node=val<node.val?node.left:node.right;return node;}

function searchBST(root, val){return solve(root, val);}
module.exports=solve;
module.exports.searchBST=searchBST;
