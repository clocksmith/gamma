// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  minDepth(root) {
    if (root === null) {
      return 0;
    }

    const queue = [root];
    let head = 0;
    let depth = 0;
    while (head < queue.length) {
      const level_end = queue.length;
      depth += 1;
      while (head < level_end) {
        const node = queue[head];
        head += 1;
        if (node.left === null && node.right === null) {
          return depth;
        }
        if (node.left !== null) {
          queue.push(node.left);
        }
        if (node.right !== null) {
          queue.push(node.right);
        }
      }
    }
    return depth;
  }
}
