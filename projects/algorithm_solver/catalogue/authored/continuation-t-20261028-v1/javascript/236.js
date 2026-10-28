function TreeNode(val){this.val=val;this.left=this.right=null;}
var lowestCommonAncestor=function(root,p,q){const parent=new Map([[root,null]]),stack=[root];while(!parent.has(p)||!parent.has(q)){const node=stack.pop();for(const child of [node.left,node.right])if(child!==null){parent.set(child,node);stack.push(child);}}const ancestors=new Set();let node=p;while(node!==null){ancestors.add(node);node=parent.get(node);}node=q;while(!ancestors.has(node))node=parent.get(node);return node;};
module.exports={lowestCommonAncestor,TreeNode};
