"use strict";
function solve(root){const balances=new Map(),stack=[[root,false]];let moves=0;while(stack.length){const [n,seen]=stack.pop();if(n==null)continue;if(!seen){stack.push([n,true],[n.left,false],[n.right,false]);continue;}const l=balances.get(n.left)||0,r=balances.get(n.right)||0;moves+=Math.abs(l)+Math.abs(r);balances.set(n,n.val-1+l+r);}return moves;}

function distributeCoins(root){return solve(root);}
module.exports=solve;
module.exports.distributeCoins=distributeCoins;
