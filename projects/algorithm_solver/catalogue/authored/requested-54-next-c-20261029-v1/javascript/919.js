"use strict";
class CBTInserter {
 constructor(root){this.nodes=[new TreeNode(root.val)];const originals=[root];for(let i=0;i<originals.length;i++){const source=originals[i],node=this.nodes[i];if(source.left){node.left=new TreeNode(source.left.val);originals.push(source.left);this.nodes.push(node.left);}if(source.right){node.right=new TreeNode(source.right.val);originals.push(source.right);this.nodes.push(node.right);}}}
 insert(val){const i=this.nodes.length,parent=this.nodes[Math.floor((i-1)/2)],child=new TreeNode(val);if(i%2)parent.left=child;else parent.right=child;this.nodes.push(child);return parent.val;}
 get_root(){return this.nodes[0];}
}
module.exports={CBTInserter};
