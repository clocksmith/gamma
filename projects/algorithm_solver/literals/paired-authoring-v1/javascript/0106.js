class TreeNode {
  constructor(val, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}


class Solution {
  buildTree(inorder, postorder) {
    if (postorder.length === 0) {
      return null;
    }
    const root = new TreeNode(postorder[postorder.length - 1]);
    const stack = [root];
    let inorderIndex = inorder.length - 1;
    for (let index = postorder.length - 2; index >= 0; index -= 1) {
      const child = new TreeNode(postorder[index]);
      if (stack[stack.length - 1].val !== inorder[inorderIndex]) {
        stack[stack.length - 1].right = child;
      } else {
        let parent = null;
        while (stack.length > 0 && stack[stack.length - 1].val === inorder[inorderIndex]) {
          parent = stack.pop();
          inorderIndex -= 1;
        }
        parent.left = child;
      }
      stack.push(child);
    }
    return root;
  }
}
