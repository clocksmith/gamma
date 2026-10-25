// External TreeNode fields: val, left, right; absent children are null.
class Solution {
  btreeGameWinningMove(root, n, x) {
    const sizes = new Map();
    const stack = [[root, false]];
    let leftSize = 0;
    let rightSize = 0;
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
        const left = node.left === null ? 0 : sizes.get(node.left);
        const right = node.right === null ? 0 : sizes.get(node.right);
        sizes.set(node, left + right + 1);
        if (node.val === x) {
          leftSize = left;
          rightSize = right;
        }
      }
    }
    const parentSize = n - leftSize - rightSize - 1;
    return Math.max(leftSize, rightSize, parentSize) * 2 > n;
  }
}
