class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class Solution{recoverTree(root){const stack=[];let current=root,previous=null,first=null,second=null;while(stack.length||current!==null){while(current!==null){stack.push(current);current=current.left;}current=stack.pop();if(previous!==null&&previous.val>current.val){if(first===null)first=previous;second=current;}previous=current;current=current.right;}[first.val,second.val]=[second.val,first.val];}}
module.exports={Solution,TreeNode};
