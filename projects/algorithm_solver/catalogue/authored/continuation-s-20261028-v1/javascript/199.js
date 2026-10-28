function TreeNode(val,left,right){this.val=val===undefined?0:val;this.left=left===undefined?null:left;this.right=right===undefined?null:right;}
var rightSideView=function(root){const queue=root===null?[]:[root],result=[];let head=0;while(head<queue.length){const end=queue.length;let node=null;while(head<end){node=queue[head++];if(node.left!==null)queue.push(node.left);if(node.right!==null)queue.push(node.right);}result.push(node.val);}return result;};
module.exports={rightSideView,TreeNode};
