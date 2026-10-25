// External TreeNode fields: val, left, right; absent children are null.
class Solution {
  sufficientSubset(root, limit) {
    if (root === null) {
      return null;
    }
    const stack = [[root, null, false, root.val, false, false]];
    while (stack.length > 0) {
      const [node, parent, isLeft, total, expanded, wasLeaf] = stack.pop();
      if (!expanded) {
        const originalLeaf = node.left === null && node.right === null;
        stack.push([node, parent, isLeft, total, true, originalLeaf]);
        if (node.right !== null) {
          stack.push([node.right, node, false, total + node.right.val, false, false]);
        }
        if (node.left !== null) {
          stack.push([node.left, node, true, total + node.left.val, false, false]);
        }
      } else {
        const insufficient = wasLeaf ? total < limit : node.left === null && node.right === null;
        if (insufficient) {
          if (parent === null) {
            root = null;
          } else if (isLeft) {
            parent.left = null;
          } else {
            parent.right = null;
          }
        }
      }
    }
    return root;
  }
}
