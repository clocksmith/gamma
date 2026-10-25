function previousVisible(text, index) {
  let skipped = 0;
  while (index >= 0) {
    if (text[index] === "#") {
      skipped += 1;
    } else if (skipped > 0) {
      skipped -= 1;
    } else {
      break;
    }
    index -= 1;
  }
  return index;
}


class Solution {
  backspaceCompare(s, t) {
    let left = s.length - 1;
    let right = t.length - 1;
    while (left >= 0 || right >= 0) {
      left = previousVisible(s, left);
      right = previousVisible(t, right);
      if (left < 0 || right < 0) {
        return left === right;
      }
      if (s[left] !== t[right]) {
        return false;
      }
      left -= 1;
      right -= 1;
    }
    return true;
  }
}
