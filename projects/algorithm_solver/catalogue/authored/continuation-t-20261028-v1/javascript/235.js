function TreeNode(val){this.val=val;this.left=this.right=null;}
var lowestCommonAncestor=function(root,p,q){const low=Math.min(p.val,q.val),high=Math.max(p.val,q.val);while(root!==null){if(root.val<low)root=root.right;else if(root.val>high)root=root.left;else return root;}};
module.exports={lowestCommonAncestor,TreeNode};
