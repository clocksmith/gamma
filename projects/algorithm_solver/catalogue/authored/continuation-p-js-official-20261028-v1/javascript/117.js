function _Node(val, left, right, next) {
    this.val = val === undefined ? null : val;
    this.left = left === undefined ? null : left;
    this.right = right === undefined ? null : right;
    this.next = next === undefined ? null : next;
}

var connect = function(root) {
let level=root;while(level!==null){let head=null,tail=null,current=level;while(current!==null){for(const child of [current.left,current.right])if(child!==null){if(tail===null)head=child;else tail.next=child;tail=child;}current=current.next;}if(tail!==null)tail.next=null;level=head;}return root;
};
module.exports = {connect, _Node};
