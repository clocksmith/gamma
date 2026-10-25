// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  removeLeafNodes(root, target) {
    if (root === null) {
      return null;
    }
    const stack = [[root, false]];
    while (stack.length > 0) {
      const [node, expanded] = stack.pop();
      if (!expanded) {
        stack.push([node, true]);
        if (node.right !== null) {
          stack.push([node.right, false]);
        }
        if (node.left !== null) {
          stack.push([node.left, false]);
        }
      } else {
        const left = node.left;
        const right = node.right;
        if (left !== null && left.val === target) {
          if (left.left === null && left.right === null) {
            node.left = null;
          }
        }
        if (right !== null && right.val === target) {
          if (right.left === null && right.right === null) {
            node.right = null;
          }
        }
      }
    }
    if (root.val === target && root.left === null && root.right === null) {
      return null;
    }
    return root;
  }
}
