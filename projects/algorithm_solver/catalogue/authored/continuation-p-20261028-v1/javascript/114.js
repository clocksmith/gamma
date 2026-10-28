class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class Solution{flatten(root){const stack=root===null?[]:[root];let previous=null;while(stack.length){const current=stack.pop();if(current.right!==null)stack.push(current.right);if(current.left!==null)stack.push(current.left);if(previous!==null){previous.left=null;previous.right=current;}previous=current;}if(previous!==null){previous.left=null;previous.right=null;}}}
module.exports={Solution,TreeNode};
