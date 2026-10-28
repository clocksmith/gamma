'use strict';
// Source-free fixed toy observations for host comparator integration.
const {observe}=require('./harness.cjs');
function ListNode(val=0,next=null){this.val=val;this.next=next;}
function TreeNode(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}
function LRUCache(capacity){this.data=new Map();}LRUCache.prototype.put=function(k,v){this.data.set(k,v);};LRUCache.prototype.get=function(k){return this.data.has(k)?this.data.get(k):-1;};
function MinStack(){this.values=[];}MinStack.prototype.push=function(v){this.values.push(v);};MinStack.prototype.pop=function(){this.values.pop();};MinStack.prototype.top=function(){return this.values.at(-1);};MinStack.prototype.getMin=function(){return Math.min(...this.values);};
function BSTIterator(root){this.root=root;}BSTIterator.prototype.next=function(){return this.root.val;};BSTIterator.prototype.hasNext=function(){return true;};
const fixtures=[
[146,{LRUCache},[['LRUCache','put','get'],[[1],[2,7],[2]]]],
[155,{MinStack},[['MinStack','push','top','getMin','pop'],[[],[-2],[],[],[]]]],
[147,{ListNode,insertionSortList:head=>{const second=head.next;second.next=head;head.next=null;return second;}},[{__list_node__:[2,1]}]],
[160,{ListNode,getIntersectionNode:(a,b)=>b},[{__list_graph__:{nodes:[{value:7,next:1},{value:7,next:null}],argument_roots:[0,1]}}]],
[173,{TreeNode,BSTIterator},[['BSTIterator','hasNext','next'],[[{__tree_node__:[3]}],[],[]]]],
[188,{maxProfit:()=>7},[1,[0,7]]]
];
process.stdout.write(JSON.stringify(fixtures.map(([pid,ns,args])=>({pid,args,record:observe(ns,pid,{args})})))+'\n');
