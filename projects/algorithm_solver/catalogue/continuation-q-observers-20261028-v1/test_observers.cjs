'use strict';
// Toy-only physical checks, deliberately no candidate imports.
const assert=require('assert'),h=require('./harness.cjs'),models=require('./identity_models.cjs');
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class ListNode{constructor(val=0,next=null){this.val=val;this.next=next;}}
class GraphNode{constructor(val=0,neighbors=[]){this.val=val;this.neighbors=neighbors;}}
class RandomNode{constructor(val,next=null,random=null){this.val=val;this.next=next;this.random=random;}}
const graph={values:[1,2],neighbors:[[1],[0]],root:0},random={values:[7,7],random:[1,0]};
function call(pid,args,method){return h.observe({[h.METHODS[pid]]:method,TreeNode,ListNode,_Node:pid===133?GraphNode:RandomNode},pid,{args});}
let count=0;function test(run){run();count++;}
test(()=>assert.throws(()=>h.observe({Solution:class{}},141,{args:[{values:[],pos:-1}]})));
test(()=>{const r=call(141,[{values:[1,1],pos:0}],function(head){assert.strictEqual(arguments.length,1);assert.strictEqual(head.next.next,head);return true;});assert.strictEqual(r.result,true);});
test(()=>{const r=call(142,[{values:[1,1],pos:1}],head=>head.next);assert.strictEqual(r.node_identity.result_original_index,1);assert.deepStrictEqual(r.alias_edges,[['result','args.0.pool.1']]);});
test(()=>assert.throws(()=>call(142,[{values:[1,1],pos:1}],()=>new ListNode(1))));
test(()=>assert.throws(()=>call(133,[graph],node=>node)));
test(()=>assert.throws(()=>call(138,[random],head=>head)));
test(()=>assert.throws(()=>call(133,[{values:[1],neighbors:[[]],root:0}],node=>new GraphNode(1,node.neighbors))));
test(()=>{const r=call(138,[random],()=>{const a=new RandomNode(7),b=new RandomNode(7);a.next=b;a.random=b;b.random=a;return a;});assert.strictEqual(r.node_identity.clone_pool.length,2);assert.deepStrictEqual(r.node_identity.clone_pool,[{value:7,next:1,random:1},{value:7,next:null,random:0}]);});
test(()=>assert.throws(()=>call(143,[{values:[1,2]}],head=>head)));
test(()=>assert.throws(()=>call(143,[{values:[1,2]}],head=>{head.next=new ListNode(2);}))); 
test(()=>assert.throws(()=>call(143,[{values:[1,2]}],head=>{head.next=null;})));
test(()=>{const r=call(143,[{values:[1,2,3]}],head=>{const b=head.next,c=b.next;head.next=c;c.next=b;b.next=null;});assert.deepStrictEqual(r.result.original_identity_order,[0,2,1]);assert.strictEqual(r.result_type,'undefined');});
test(()=>{const r=call(140,['a',['a']],(s,words)=>words);assert.deepStrictEqual(r.alias_edges,[['result','args.1']]);});
test(()=>assert.throws(()=>call(142,[{values:[1],pos:0}],head=>{Object.defineProperty(head,'next',{get:()=>head});return head;})));
test(()=>{try{assert.throws(()=>call(142,[{values:[1],pos:0}],head=>{ListNode.prototype.extra=1;return head;}));}finally{delete ListNode.prototype.extra;}});
test(()=>{for(const [pid,args] of [[133,[{values:[],neighbors:[],root:null}]],[138,[{values:[],random:[]}]],[142,[{values:[],pos:-1}]]]){const r=call(pid,args,()=>null);assert.strictEqual(r.node_identity.original_node_count,0);}});
test(()=>{const [head,pool]=models.materialize(143,{values:[1,2,3]},ListNode);const third=head.next.next;head.next.next=null;third.next=head.next;head.next=third;assert.deepStrictEqual(models.reordered(head,pool,undefined).original_identity_order,[0,2,1]);});
console.log(`${count} source-free JS Q controls passed`);
