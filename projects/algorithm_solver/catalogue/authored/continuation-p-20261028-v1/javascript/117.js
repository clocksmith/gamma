class Node{constructor(val=0,left=null,right=null,next=null){this.val=val;this.left=left;this.right=right;this.next=next;}}
class Solution{connect(root){let level=root;while(level!==null){let head=null,tail=null,current=level;while(current!==null){for(const child of [current.left,current.right])if(child!==null){if(tail===null)head=child;else tail.next=child;tail=child;}current=current.next;}if(tail!==null)tail.next=null;level=head;}return root;}}
module.exports={Solution,Node};
