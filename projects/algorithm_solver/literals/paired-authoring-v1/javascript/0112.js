// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  hasPathSum(root, targetSum) {
    if (root === null) {
      return false;
    }

    const stack = [[root, root.val]];
    while (stack.length > 0) {
      const [node, total] = stack.pop();
      if (node.left === null && node.right === null) {
        if (total === targetSum) {
          return true;
        }
      }
      if (node.right !== null) {
        stack.push([node.right, total + node.right.val]);
      }
      if (node.left !== null) {
        stack.push([node.left, total + node.left.val]);
      }
    }
    return false;
  }
}
