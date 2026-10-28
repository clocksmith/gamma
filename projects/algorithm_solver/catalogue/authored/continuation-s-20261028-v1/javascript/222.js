function TreeNode(val,left,right){this.val=val===undefined?0:val;this.left=left===undefined?null:left;this.right=right===undefined?null:right;}
var countNodes=function(root){if(root===null)return 0;function height(node){let result=0;while(node!==null){result++;node=node.left;}return result;}const left=height(root.left),right=height(root.right);return left===right?2**left+countNodes(root.right):2**right+countNodes(root.left);};
module.exports={countNodes,TreeNode};
