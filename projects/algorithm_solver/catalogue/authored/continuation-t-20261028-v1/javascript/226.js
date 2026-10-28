function TreeNode(val,left,right){this.val=val===undefined?0:val;this.left=left===undefined?null:left;this.right=right===undefined?null:right;}
var invertTree=function(root){const stack=root===null?[]:[root];while(stack.length){const node=stack.pop();[node.left,node.right]=[node.right,node.left];if(node.left!==null)stack.push(node.left);if(node.right!==null)stack.push(node.right);}return root;};
module.exports={invertTree,TreeNode};
