class Solution {
  numberOfLines(widths, s) {
    let lines = 1;
    let used = 0;
    for (let index = 0; index < s.length; index += 1) {
      const width = widths[s.charCodeAt(index) - 97];
      if (used + width > 100) {
        lines += 1;
        used = 0;
      }
      used += width;
    }
    return [lines, used];
  }
}
