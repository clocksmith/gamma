class Node{constructor(val=0,left=null,right=null,next=null){this.val=val;this.left=left;this.right=right;this.next=next;}}
class Solution{connect(root){let level=root;while(level!==null&&level.left!==null){let current=level;while(current!==null){current.left.next=current.right;current.right.next=current.next!==null?current.next.left:null;current=current.next;}level=level.left;}return root;}}
module.exports={Solution,Node};
