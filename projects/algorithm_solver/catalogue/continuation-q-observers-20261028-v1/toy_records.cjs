'use strict';
// Fixed synthetic fixtures. No numbered candidate module is loaded.
const h=require('./harness.cjs');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class ListNode{constructor(val=0,next=null){this.val=val;this.next=next;}}
class GraphNode{constructor(val=0,neighbors=[]){this.val=val;this.neighbors=neighbors;}}
class RandomNode{constructor(val,next=null,random=null){this.val=val;this.next=next;this.random=random;}}
const graph={values:[1,2,3],neighbors:[[1,2],[0,2],[0,1]],root:0},random={values:[7,7],random:[1,0]},tree={values:[1,2,3],left:[1,null,null],right:[2,null,null],root:0};
function graphClone(){const a=new GraphNode(1),b=new GraphNode(2),c=new GraphNode(3);a.neighbors=[c,b];b.neighbors=[c,a];c.neighbors=[b,a];return a;}
function randomClone(){const a=new RandomNode(7),b=new RandomNode(7);a.next=b;a.random=b;b.random=a;return a;}
function reorderFour(head){const b=head.next,c=b.next,d=c.next;head.next=d;d.next=b;b.next=c;c.next=null;}
function call(pid,args,method){return h.observe({[h.METHODS[pid]]:method,TreeNode,ListNode,_Node:pid===133?GraphNode:RandomNode},pid,{args});}
function emit(pid,args,method,label,accepted=true){const record=call(pid,args,method);process.stdout.write(JSON.stringify({pid,args,record,label,accepted})+'\n');return record;}
emit(126,['aa','bb',['ab','ba','bb']],function(){return [['aa','ba','bb'],['aa','ab','bb']];},'unordered-ladders');
emit(129,[tree],function(){return 25;},'readonly-tree-sum');
emit(132,['aab'],function(){return 1;},'cut-scalar');
const record=emit(133,[graph],graphClone,'permuted-graph-neighbors');
emit(138,[random],randomClone,'random-cycle-shared-targets');
emit(140,['aa',['a','aa']],function(){return ['aa','a a'];},'unordered-sentences');
emit(141,[{values:[1,1,1],pos:1}],function(head){if(arguments.length!==1)throw Error('pos leaked as method argument');return true;},'head-only-cycle');
emit(142,[{values:[1,1,1],pos:1}],function(head){if(arguments.length!==1)throw Error('pos leaked as method argument');return head.next;},'original-entry');
emit(143,[{values:[1,2,3,4]}],reorderFour,'same-original-pool');
emit(144,[tree],function(){return [1,2,3];},'readonly-preorder');
for(const change of ['collapsed','missing','duplicate']){const bad=structuredClone(record),rows=bad.node_identity.clone_pool;if(change==='collapsed')rows[1].value=rows[2].value;else if(change==='missing')rows[0].neighbors.pop();else rows[0].neighbors=[rows[0].neighbors[0],rows[0].neighbors[0]];bad.result.__clone_pool__=rows;process.stdout.write(JSON.stringify({pid:133,args:[graph],record:bad,label:change,accepted:false})+'\n');}
emit(126,['a','c',['c']],function(){return [['a','c'],['a','c']];},'duplicate-ladders',false);
emit(140,['a',['a']],function(){return ['a','a'];},'duplicate-sentences',false);
emit(129,[tree],function(root){root.val=9;return 25;},'mutated-original-tree',false);
emit(142,[{values:[1,1,1],pos:1}],function(head){return head.next.next;},'wrong-same-value-original-entry',false);
module.exports={call,graph,random,tree,graphClone,randomClone,reorderFour};
