"use strict";
function solve(n){if(n%2===0)return [];const memo=new Map([[1,[null]]]);
 function shapes(size){if(memo.has(size))return memo.get(size);const out=[];for(let l=1;l<size;l+=2)for(const a of shapes(l))for(const b of shapes(size-1-l))out.push([a,b]);memo.set(size,out);return out;}
 function build(shape){const node=new TreeNode(0);if(shape!==null){node.left=build(shape[0]);node.right=build(shape[1]);}return node;}
 return shapes(n).map(build);
}

function allPossibleFBT(n) { return solve(n); }
module.exports=solve;
module.exports.allPossibleFBT=allPossibleFBT;
