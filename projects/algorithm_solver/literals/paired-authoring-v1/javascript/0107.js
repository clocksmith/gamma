// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  levelOrderBottom(root) {
    if (root === null) {
      return [];
    }

    const queue = [root];
    let head = 0;
    const levels = [];
    while (head < queue.length) {
      const level_end = queue.length;
      const level = [];
      while (head < level_end) {
        const node = queue[head];
        head += 1;
        level.push(node.val);
        if (node.left !== null) {
          queue.push(node.left);
        }
        if (node.right !== null) {
          queue.push(node.right);
        }
      }
      levels.push(level);
    }
    levels.reverse();
    return levels;
  }
}
