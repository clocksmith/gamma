"use strict";
class _Node {constructor(val,next=null,random=null){this.val=val;this.next=next;this.random=random;}}
function solve(head) {
const clones=new Map([[null,null]]);let current=head;while(current!==null){clones.set(current,new _Node(current.val));current=current.next;}current=head;while(current!==null){clones.get(current).next=clones.get(current.next);clones.get(current).random=clones.get(current.random);current=current.next;}return clones.get(head);
}
function copyRandomList(head) { return solve(head); }
class Solution {copyRandomList(head) { return solve(head); }}
module.exports=solve;
module.exports.copyRandomList=copyRandomList;
module.exports.Solution=Solution;
module.exports._Node=_Node;
module.exports.Node=_Node;
