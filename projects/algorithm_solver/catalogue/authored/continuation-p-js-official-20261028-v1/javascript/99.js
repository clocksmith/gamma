function TreeNode(val, left, right) {
    this.val = (val === undefined ? 0 : val);
    this.left = (left === undefined ? null : left);
    this.right = (right === undefined ? null : right);
}

var recoverTree = function(root) {
const stack=[];let current=root,previous=null,first=null,second=null;while(stack.length||current!==null){while(current!==null){stack.push(current);current=current.left;}current=stack.pop();if(previous!==null&&previous.val>current.val){if(first===null)first=previous;second=current;}previous=current;current=current.right;}[first.val,second.val]=[second.val,first.val];
};
module.exports = {recoverTree, TreeNode};
