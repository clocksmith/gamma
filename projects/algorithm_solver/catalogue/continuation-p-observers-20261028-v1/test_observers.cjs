'use strict';
// Toy constructors/wrappers only; never require a numbered candidate.
const assert=require('assert'),h=require('./harness.cjs');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class Node{constructor(val=0,left=null,right=null,next=null){this.val=val;this.left=left;this.right=right;this.next=next;}}
function call(pid,args,method){class Solution{}Object.defineProperty(Solution.prototype,h.METHODS[pid],{value:method,writable:true,configurable:true});return h.observe({Solution,TreeNode,Node},pid,{args});}
let controls=0;function test(run){run();controls++;}
test(()=>{for(const [pid,args,value] of [[17,['23'],['ad','ae']],[65,['1'],true],[87,['a','a'],true]]){const r=call(pid,args,function(){return value;});assert.deepStrictEqual(r.result,value);assert.deepStrictEqual(r.args_before,r.args_after);}});
test(()=>assert.throws(()=>h.observe({solve:()=>true},65,{args:['1']})));
test(()=>{const r=call(37,[Array.from({length:9},()=>Array(9).fill('.'))],function(board){board[0]=Array(9).fill('1');});assert.strictEqual(r.result_type,'undefined');assert.strictEqual(r.result,null);assert.strictEqual(r.board_identity.argument_root_preserved,true);});
test(()=>assert.throws(()=>call(37,[Array.from({length:9},()=>Array(9).fill('.'))],function(board){return board;})));
test(()=>{const r=call(99,[{__tree_node__:[1,2,3]}],function(root){[root.val,root.left.val]=[root.left.val,root.val];});assert.deepStrictEqual(r.args_after,[{__tree_node__:[2,1,3]}]);assert.deepStrictEqual(r.node_identity.after.map(n=>n.id),[0,1,2]);});
test(()=>{const r=call(114,[{__tree_node__:[1,2]}],function(root){root.right=root.left;root.left=null;});assert.strictEqual(r.node_identity.after[0].right,1);assert.strictEqual(r.node_identity.after[0].left,null);});
test(()=>{for(const pid of [116,117]){const r=call(pid,[{__next_node__:[1,2,3]}],function(root){root.left.next=root.right;return root;});assert.strictEqual(r.node_identity.result_root,0);assert.strictEqual(r.node_identity.after[1].next,2);assert.deepStrictEqual(r.alias_edges,[['result','args.0']]);}});
test(()=>assert.throws(()=>call(117,[{__next_node__:[1]}],function(){return new Node(1);}))); 
test(()=>{const r=call(95,[3],function(){const shared=new TreeNode(1);return [new TreeNode(2,shared),new TreeNode(3,shared)];});assert.strictEqual(r.node_integrity.checked_node_count,3);assert.strictEqual(r.node_identity.after[0].left,r.node_identity.after[2].left);});
test(()=>{assert.throws(()=>call(95,[2],function(){const child=new TreeNode(1);return [new TreeNode(2,child,child)];}));assert.throws(()=>call(95,[1],function(){const root=new TreeNode(1);root.left=root;return [root];}));});
test(()=>{const r=call(108,[[1,2]],function(){return new TreeNode(1,null,new TreeNode(2));});assert.deepStrictEqual(r.result,{__tree_node__:[1,null,2]});assert.deepStrictEqual(r.args_after,[[1,2]]);});
test(()=>assert.throws(()=>call(99,[{__tree_node__:[1]}],function(root){Object.defineProperty(root,'val',{get:()=>1});})));
test(()=>{try{assert.throws(()=>call(99,[{__tree_node__:[1]}],function(){TreeNode.prototype.extra=1;}));}finally{delete TreeNode.prototype.extra;}});
test(()=>assert.throws(()=>call(117,[{__next_node__:[1]}],function(root){root.next=root;return root;})));
test(()=>{const r=call(99,[{__tree_node__:[2,1]}],function(root){root.left=null;});assert.strictEqual(r.node_identity.after.length,2);});
test(()=>{const r=call(117,[{__next_node__:[]}],function(root){return root;});assert.deepStrictEqual(r.node_identity.argument_roots,[null]);assert.deepStrictEqual(r.alias_edges,[]);});
console.log(`${controls} source-free JS observer controls passed`);
