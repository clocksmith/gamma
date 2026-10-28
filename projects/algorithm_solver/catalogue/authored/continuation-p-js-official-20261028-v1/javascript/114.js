function TreeNode(val, left, right) {
    this.val = (val === undefined ? 0 : val);
    this.left = (left === undefined ? null : left);
    this.right = (right === undefined ? null : right);
}

var flatten = function(root) {
const stack=root===null?[]:[root];let previous=null;while(stack.length){const current=stack.pop();if(current.right!==null)stack.push(current.right);if(current.left!==null)stack.push(current.left);if(previous!==null){previous.left=null;previous.right=current;}previous=current;}if(previous!==null){previous.left=null;previous.right=null;}
};
module.exports = {flatten, TreeNode};
