// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  maxPathSum(root) {
    if (root === null) {
      return 0;
    }

    let best = root.val;
    const stack = [[root, false]];
    const gains = [];
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
        continue;
      }

      const right_gain = node.right !== null ? gains.pop() : 0;
      const left_gain = node.left !== null ? gains.pop() : 0;
      best = Math.max(best, node.val + left_gain + right_gain);
      gains.push(Math.max(0, node.val + Math.max(left_gain, right_gain)));
    }
    return best;
  }
}
