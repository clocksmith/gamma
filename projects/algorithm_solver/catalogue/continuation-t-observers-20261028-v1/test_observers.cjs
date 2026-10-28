"use strict";
// Synthetic fixtures/functions only; never requires a numbered candidate file.
const assert=require('assert'),{observe}=require('./harness.cjs');let count=0;const records=[];
function test(name,fn){fn();count++;}
function TreeNode(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}
function ListNode(val=0,next=null){this.val=val;this.next=next;}
function requiredTree(){return function TreeNode(val){this.val=val;this.left=null;this.right=null;};}
function requiredList(){return function ListNode(val){this.val=val;this.next=null;};}
// FIFO abstract toy, not stack-only candidate implementation evidence.
function MyQueue(){this.items=[];}
MyQueue.prototype.push=function(x){this.items.push(x);};MyQueue.prototype.pop=function(){return this.items.shift();};MyQueue.prototype.peek=function(){return this.items[0];};MyQueue.prototype.empty=function(){return this.items.length===0;};
const TREE={values:[2,1,3],left:[1,null,null],right:[2,null,null],root:0};
function accept(pid,args,namespace){const record=observe(namespace,pid,{args});records.push({pid,args,record});return record;}
test('226 original mirror',()=>{const record=accept(226,[TREE],{TreeNode,invertTree:function(root){[root.left,root.right]=[root.right,root.left];return root;}});assert.strictEqual(record.result.original_id,0);});
test('226 empty',()=>accept(226,[{values:[],left:[],right:[],root:null}],{TreeNode,invertTree:function(root){return root;}}));
test('230 readonly',()=>accept(230,[TREE,2],{TreeNode,kthSmallest:function(root,k){return root.val;}}));
test('232 typed state',()=>accept(232,[['MyQueue','push','push','peek','pop','empty','pop','empty'],[[],[1],[2],[],[],[],[],[]]],{MyQueue}));
test('233 scalar',()=>accept(233,[13],{countDigitOne:function(n){return 6;}}));
test('234 restoration',()=>accept(234,[{values:[1,2,1],next:[1,2,null],head:0}],{ListNode,isPalindrome:function(head){return true;}}));
test('235 p/q original aliases',()=>{const record=accept(235,[TREE,0,2],{TreeNode:requiredTree(),lowestCommonAncestor:function(root,p,q){return p;}});assert(record.alias_edges.some(row=>row[1]==='args.1'));});
test('236 nonroot p alias',()=>accept(236,[{values:[10,30,20,40],left:[1,3,null,null],right:[2,null,null,null],root:0},1,3],{TreeNode:requiredTree(),lowestCommonAncestor:function(root,p,q){return p;}}));
test('237 target ONLY actual arg',()=>{const record=accept(237,[{values:[1,2,3,4],next:[1,2,3,null],head:0},1],{ListNode:requiredList(),deleteNode:function(node){assert.strictEqual(arguments.length,1);assert.strictEqual(node.val,2);node.val=3;node.next=node.next.next;}});assert.deepStrictEqual(record.node_identity.argument_roots,[1]);assert.deepStrictEqual(record.node_identity.fixture_roots,[0]);assert.deepStrictEqual(record.result.order,[0,1,3]);});
test('premium excluded',()=>{for(const pid of [243,245])assert.throws(()=>observe({},pid,{args:[]}),/fixed T/);});
test('equalvalued clone rejected',()=>{const Node=requiredTree();assert.throws(()=>observe({TreeNode:Node,lowestCommonAncestor:function(root,p,q){return new Node(p.val);}},235,{args:[TREE,0,2]}),/original identity/);});
test('237 actual undefined',()=>assert.throws(()=>observe({ListNode:requiredList(),deleteNode:function(node){node.val=3;node.next=null;return node;}},237,{args:[{values:[1,2,3],next:[1,2,null],head:0},1]}),/undefined/));
test('wrong queue void',()=>{function BadQueue(){}BadQueue.prototype.push=function(x){return null;};assert.throws(()=>observe({MyQueue:BadQueue},232,{args:[['MyQueue','push'],[[],[1]]]}),/undefined/);});
test('no solve fallback',()=>assert.throws(()=>observe({solve:function(n){return 6;}},233,{args:[13]}),/original own exported/));
test('inherited function rejected',()=>assert.throws(()=>observe(Object.create({countDigitOne:function(n){return 6;}}),233,{args:[13]}),/original own exported/));
test('field flag mutation rejected',()=>assert.throws(()=>observe({TreeNode:requiredTree(),lowestCommonAncestor:function(root,p,q){Object.defineProperty(p,'val',{writable:false});return p;}},235,{args:[TREE,0,2]}),/descriptors changed/));
test('fresh class traces',()=>{const args=[['MyQueue','empty'],[[],[]]];accept(232,args,{MyQueue});accept(232,args,{MyQueue});});
test('original constructor required',()=>assert.throws(()=>observe({lowestCommonAncestor:function(root,p,q){return p;}},235,{args:[TREE,0,2]}),/original own exported/));
if(process.argv.includes('--records'))process.stdout.write(JSON.stringify({tests:count,records}));else process.stdout.write(JSON.stringify({source_free_toy_tests:count,candidate_executions:0})+'\n');
