// External TreeNode shape: {val: number, left: TreeNode | null, right: TreeNode | null}.
class Solution {
  increasingBST(root) {
    const stack = [];
    let current = root;
    let head = null;
    let tail = null;
    while (current !== null || stack.length > 0) {
      while (current !== null) {
        stack.push(current);
        current = current.left;
      }
      const node = stack.pop();
      current = node.right;
      node.left = null;
      if (tail === null) {
        head = node;
      } else {
        tail.right = node;
      }
      tail = node;
    }
    if (tail !== null) {
      tail.right = null;
    }
    return head;
  }
}
