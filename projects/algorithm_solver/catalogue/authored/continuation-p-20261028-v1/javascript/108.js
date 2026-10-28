class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
class Solution{sortedArrayToBST(nums){function build(lo,hi){if(lo>=hi)return null;const middle=Math.floor((lo+hi)/2);return new TreeNode(nums[middle],build(lo,middle),build(middle+1,hi));}return build(0,nums.length);}}
module.exports={Solution,TreeNode};
