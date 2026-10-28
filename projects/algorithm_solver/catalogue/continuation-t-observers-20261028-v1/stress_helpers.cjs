"use strict";
//100k-node SOURCE-FREE helper stress only. No real candidate module loaded.
const assert=require('assert'),{observe}=require('./harness.cjs'),started=Date.now(),mode=process.argv[2],n=100000;
let record,args;
if(mode==='tree'){
 function TreeNode(val){this.val=val;this.left=null;this.right=null;}
 const packet={values:Array.from({length:n},(_,i)=>i),left:Array(n).fill(null),right:Array.from({length:n},(_,i)=>i+1<n?i+1:null),root:0};args=[packet,50000,n-1];
 record=observe({TreeNode,lowestCommonAncestor:function(root,p,q){return p;}},235,{args});assert.strictEqual(record.result.original_id,50000);assert(record.alias_edges.some(edge=>edge[1]==='args.1'));
}else if(mode==='list'){
 function ListNode(val=0,next=null){this.val=val;this.next=next;}
 const packet={values:Array(n).fill(1),next:Array.from({length:n},(_,i)=>i+1<n?i+1:null),head:0};args=[packet];
 record=observe({ListNode,isPalindrome:function(head){return true;}},234,{args});assert.strictEqual(record.result,true);
}else throw Error('fixed stress mode tree/list');
assert.strictEqual(record.node_identity.before.length,n);assert.strictEqual(record.node_identity.after.length,n);assert.deepStrictEqual(record.node_identity.before,record.node_identity.after);
process.stdout.write(JSON.stringify({schema:'gamma.t-local-helper-stress.v1',mode,nodes:n,elapsed_ms:Date.now()-started,record_json_bytes:Buffer.byteLength(JSON.stringify(record)),peak_process_memory_bytes:process.resourceUsage().maxRSS*1024,node_version:process.version,node_flags:process.execArgv,candidate_executions:0,linux_qualification:false})+'\n');
