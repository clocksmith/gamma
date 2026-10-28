'use strict';
const assert=require('assert'),{observe}=require('./harness.cjs');
function TreeNode(val,left,right){this.val=val===undefined?0:val;this.left=left===undefined?null:left;this.right=right===undefined?null:right;}
const args=[{values:[1,2,2],left:[1,null,null],right:[2,null,null],root:0}],ns={TreeNode,binaryTreePaths:function(root){assert(root instanceof TreeNode);assert.notStrictEqual(root.left,root.right);return ['1->2','1->2'];}};
const row=observe(ns,257,{args});assert.deepStrictEqual(row.result,['1->2','1->2']);assert.deepStrictEqual(row.node_identity.before,row.node_identity.after);assert.strictEqual(row.entry_kind,'javascript-official-function');
for(const pid of [true,246,259])assert.throws(()=>observe(ns,pid,{args}));
assert.throws(()=>observe({TreeNode,solve(){return[];}},257,{args}));
assert.throws(()=>observe({TreeNode,binaryTreePaths:function(){return[true];}},257,{args}));
assert.throws(()=>observe({TreeNode:function(val=7,left=null,right=null){this.val=val;this.left=left;this.right=right;},binaryTreePaths:function(){return[];}},257,{args}));
const mut=observe({TreeNode,binaryTreePaths:function(root){root.val=99;return ['1->2','1->2'];}},257,{args});assert.notDeepStrictEqual(mut.node_identity.before,mut.node_identity.after);
const bad=JSON.parse(JSON.stringify(args));bad[0].left[0]=true;assert.throws(()=>observe(ns,257,{args:bad}));
assert.throws(()=>observe(ns,257,{args,expected:[]}));
process.stdout.write(JSON.stringify(row)+'\n');console.error('10 source-free JavaScript controls passed');
