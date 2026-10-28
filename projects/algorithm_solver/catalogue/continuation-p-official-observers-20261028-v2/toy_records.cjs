'use strict';
// Fixed synthetic wrapper fixtures, not candidate algorithms or qualification cases.
const h=require('./harness.cjs');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class Node{constructor(val=0,left=null,right=null,next=null){this.val=val;this.left=left;this.right=right;this.next=next;}}
const board=Array.from({length:9},(_,r)=>Array.from({length:9},(_,c)=>String((r*3+Math.floor(r/3)+c)%9+1)));
const fixtures=[
[17,['2'],function(){return ['c','a','b'];}],
[37,[board],function(){}],
[65,['1'],function(){return true;}],
[87,['a','a'],function(){return true;}],
[95,[1],function(){return [new TreeNode(1)];}],
[99,[{__tree_node__:[1,2,3]}],function(root){[root.val,root.left.val]=[root.left.val,root.val];}],
[108,[[1,2]],function(){return new TreeNode(1,null,new TreeNode(2));}],
[114,[{__tree_node__:[1,2]}],function(root){root.right=root.left;root.left=null;}],
[116,[{__next_node__:[1,2,3]}],function(root){root.left.next=root.right;return root;}],
[117,[{__next_node__:[1,2,3]}],function(root){root.left.next=root.right;return root;}]];
for(const [pid,args,method] of fixtures){const record=h.observe({[h.METHODS[pid]]:method,TreeNode,_Node:Node},pid,{args});process.stdout.write(JSON.stringify({pid,args,record})+'\n');}
