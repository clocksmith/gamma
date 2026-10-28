function TreeNode(val, left, right) {
    this.val = (val === undefined ? 0 : val);
    this.left = (left === undefined ? null : left);
    this.right = (right === undefined ? null : right);
}

var sortedArrayToBST = function(nums) {
function build(lo,hi){if(lo>=hi)return null;const middle=Math.floor((lo+hi)/2);return new TreeNode(nums[middle],build(lo,middle),build(middle+1,hi));}return build(0,nums.length);
};
module.exports = {sortedArrayToBST, TreeNode};
