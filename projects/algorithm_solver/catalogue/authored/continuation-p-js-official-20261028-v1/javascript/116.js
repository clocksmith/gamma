function _Node(val, left, right, next) {
    this.val = val === undefined ? null : val;
    this.left = left === undefined ? null : left;
    this.right = right === undefined ? null : right;
    this.next = next === undefined ? null : next;
}

var connect = function(root) {
let level=root;while(level!==null&&level.left!==null){let current=level;while(current!==null){current.left.next=current.right;current.right.next=current.next!==null?current.next.left:null;current=current.next;}level=level.left;}return root;
};
module.exports = {connect, _Node};
