"use strict";
// Synthetic protocol toys only; never requires a numbered candidate module.
const assert=require('assert'),{observe}=require('./harness.cjs');let count=0;const records=[];
function test(name,fn){fn();count++;}
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class ListNode{constructor(val=0,next=null){this.val=val;this.next=next;}}
class Trie{constructor(){this.words=new Set();}insert(word){this.words.add(word);}search(word){return this.words.has(word);}startsWith(prefix){return [...this.words].some(word=>word.startsWith(prefix));}}
class WordDictionary{constructor(){this.words=new Set();}addWord(word){this.words.add(word);}search(word){return [...this.words].some(w=>word.length===w.length&&[...word].every((c,i)=>c==='.'||c===w[i]));}}
// Abstract toy model, not a queue-only candidate implementation.
class MyStack{constructor(){this.items=[];}push(x){this.items.push(x);}pop(){return this.items.pop();}top(){return this.items[this.items.length-1];}empty(){return this.items.length===0;}}
const TREE={values:[1,2,3],left:[1,null,null],right:[2,null,null],root:0},LIST={values:[1,2,1,3],next:[1,2,3,null],head:0};
function accept(pid,args,namespace){const record=observe(namespace,pid,{args});records.push({pid,args,record});return record;}
test('199 original tree',()=>{const record=accept(199,[TREE],{TreeNode,rightSideView:function(root){return [root.val,root.right.val];}});assert.deepStrictEqual(record.result,[1,3]);});
test('222 complete tree',()=>{assert.strictEqual(accept(222,[TREE],{TreeNode,countNodes:function(root){return 3;}}).result,3);});
test('203 removed external/cyclic pointers',()=>{const record=accept(203,[LIST,1],{ListNode,removeElements:function(head,val){const kept=head.next,removed=kept.next,last=removed.next;kept.next=last;head.next=new ListNode(9);removed.next=removed;return kept;}});assert.deepStrictEqual(record.result.order,[1,3]);assert.deepStrictEqual(record.node_identity.after[0].next,{external_identity:0});});
test('206 same original pool',()=>{const packet={values:[1,1,1],next:[1,2,null],head:0};const record=accept(206,[packet],{ListNode,reverseList:function(head){const b=head.next,c=b.next;c.next=b;b.next=head;head.next=null;return c;}});assert.deepStrictEqual(record.result.order,[2,1,0]);});
test('clone rejected',()=>assert.throws(()=>observe({ListNode,reverseList:function(head){return new ListNode(head.val);}},206,{args:[{values:[1],next:[null],head:0}]}),/original identity/));
test('all design traces',()=>{for(const [pid,args] of [[208,[['Trie','insert','search','search','startsWith'],[[],['apple'],['apple'],['app'],['app']]]],[211,[['WordDictionary','addWord','search','search'],[[],['bad'],['.ad'],['b..']]]],[225,[['MyStack','push','push','top','pop','empty'],[[],[1],[2],[],[],[]]]]])accept(pid,args,{Trie,WordDictionary,MyStack});});
test('fresh design traces',()=>{const args=[['Trie','search'],[[],['a']]];accept(208,args,{Trie});accept(208,args,{Trie});});
test('wrong primitive type',()=>{class BadTrie{search(word){return 1;}}assert.throws(()=>observe({Trie:BadTrie},208,{args:[['Trie','search'],[[],['a']]]}),/boolean/);});
test('wrong void type',()=>{class BadTrie{insert(word){return null;}}assert.throws(()=>observe({Trie:BadTrie},208,{args:[['Trie','insert'],[[],['a']]]}),/undefined/);});
test('no solve fallback',()=>assert.throws(()=>observe({solve:function(){return 0;}},214,{args:['a']}),/original own exported/));
test('unordered readonly board',()=>{const r=accept(212,[[['a','b']],['a','ab','z']],{findWords:function(board,words){return ['ab','a'];}});assert.deepStrictEqual(r.args_before,r.args_after);});
test('legal alias of word input',()=>{const r=accept(212,[[['a']],['a']],{findWords:function(board,words){return words;}});assert.deepStrictEqual(r.alias_edges,[['result','args.1']]);});
test('scalar routes',()=>{accept(214,['aacecaaa'],{shortestPalindrome:function(s){return 'aaacecaaa';}});accept(224,['(1+2)'],{calculate:function(s){return 3;}});});
test('inherited official export rejected',()=>{const namespace=Object.create({calculate:function(s){return 3;}});assert.throws(()=>observe(namespace,224,{args:['(1+2)']}),/original own exported/);});
test('wrong constructor defaults rejected',()=>{class BadTree{constructor(val=5,left=null,right=null){this.val=val;this.left=left;this.right=right;}}assert.throws(()=>observe({TreeNode:BadTree,countNodes:function(root){return 3;}},222,{args:[TREE]}),/constructor defaults/);});
test('native own descriptor mutation rejected',()=>{assert.throws(()=>observe({TreeNode,rightSideView:function(root){Object.defineProperty(root,'val',{writable:false});return [1,3];}},199,{args:[TREE]}),/descriptors changed/);});
test('retained returned cycle rejected',()=>{assert.throws(()=>observe({ListNode,reverseList:function(head){head.next=head;return head;}},206,{args:[{values:[1],next:[null],head:0}]}),/cycle/);});
if(process.argv.includes('--records'))process.stdout.write(JSON.stringify({tests:count,records}));else process.stdout.write(JSON.stringify({source_free_toy_tests:count,candidate_executions:0})+'\n');
