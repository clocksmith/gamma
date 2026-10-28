'use strict';
// Inert helper stress only: no authored program is read/required/executed.
const v8=require('v8'),{observe}=require('../continuation-r-observers-20261028-v1/harness.cjs');
function TreeNode(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}
function BSTIterator(root){this.root=root;}
BSTIterator.prototype.hasNext=function(){return true;};
BSTIterator.prototype.next=function(){return this.root.val;};
const start=process.hrtime.bigint(),values=[0];
for(let i=1;i<100000;i++)values.push(null,i);
const args=[['BSTIterator','hasNext'],[[{__tree_node__:values}],[]]];
const record=observe({TreeNode,BSTIterator},173,{args});
const bytes=Buffer.byteLength(JSON.stringify({i:0,...record})+'\n');
if(record.node_identity.after.length!==100000||bytes>14508404)throw Error('fixed helper node/output control failed');
process.stdout.write(JSON.stringify({scope:'inert native-helper stress; not Linux qualification or aggregate memory cap',nodes:record.node_identity.after.length,actual_record_bytes:bytes,elapsed_seconds:Number(process.hrtime.bigint()-start)/1e9,observed_process_rss_bytes:process.memoryUsage().rss,heap_size_limit_bytes:v8.getHeapStatistics().heap_size_limit,node_version:process.version,node_flags:process.execArgv,candidate_sources_loaded:0,candidate_executions:0})+'\n');
